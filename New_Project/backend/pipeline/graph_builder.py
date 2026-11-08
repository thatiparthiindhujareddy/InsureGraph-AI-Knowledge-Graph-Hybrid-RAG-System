"""
InsureGraph AI — Knowledge Graph Builder
Builds and manages a NetworkX-based knowledge graph for insurance entities.
"""
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict

import networkx as nx

from backend.config import settings
from backend.models.entities import InsuranceEntity, InsuranceRelationship, EntityType

logger = logging.getLogger(__name__)


class InsuranceKnowledgeGraph:
    """
    NetworkX-based knowledge graph for P&C insurance policy entities.
    Supports multi-hop traversal and neighborhood queries.
    """

    def __init__(self, persist_path: Optional[str] = None):
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self.persist_path = persist_path or settings.graph_persist_path
        self._document_nodes: Dict[str, Set[str]] = defaultdict(set)  # doc_id -> node_ids

        # Try to load existing graph
        self._load()

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load(self):
        """Load graph from disk if it exists."""
        path = Path(self.persist_path)
        if path.exists():
            try:
                with open(path, "rb") as f:
                    data = pickle.load(f)
                    self.graph = data["graph"]
                    self._document_nodes = data.get("document_nodes", defaultdict(set))
                logger.info(
                    f"Loaded knowledge graph: {self.graph.number_of_nodes()} nodes, "
                    f"{self.graph.number_of_edges()} edges"
                )
            except Exception as e:
                logger.warning(f"Could not load graph from {path}: {e}. Starting fresh.")
                self.graph = nx.MultiDiGraph()

    def save(self):
        """Persist graph to disk."""
        path = Path(self.persist_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(
                {"graph": self.graph, "document_nodes": dict(self._document_nodes)},
                f,
            )
        logger.info(f"Graph saved: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")

    # ── Graph Building ─────────────────────────────────────────────────────────

    def add_entities(self, entities: List[InsuranceEntity]) -> int:
        """Add insurance entities as nodes to the graph. Returns count added."""
        added = 0
        for entity in entities:
            if not self.graph.has_node(entity.id):
                self.graph.add_node(
                    entity.id,
                    label=entity.label,
                    entity_type=entity.entity_type.value,
                    properties=entity.properties,
                    source_text=entity.source_text,
                    document_id=entity.document_id,
                    page_number=entity.page_number,
                    confidence=entity.confidence,
                )
                self._document_nodes[entity.document_id].add(entity.id)
                added += 1
            else:
                # Merge properties
                existing = self.graph.nodes[entity.id]
                existing["properties"].update(entity.properties)
        return added

    def add_relationships(self, relationships: List[InsuranceRelationship]) -> int:
        """Add relationships as directed edges. Returns count added."""
        added = 0
        for rel in relationships:
            if (
                self.graph.has_node(rel.source_id)
                and self.graph.has_node(rel.target_id)
            ):
                self.graph.add_edge(
                    rel.source_id,
                    rel.target_id,
                    relationship_type=rel.relationship_type.value,
                    properties=rel.properties,
                    source_text=rel.source_text,
                    confidence=rel.confidence,
                )
                added += 1
        return added

    def build_from_extraction(
        self,
        entities: List[InsuranceEntity],
        relationships: List[InsuranceRelationship],
    ) -> Tuple[int, int]:
        """Convenience method: add entities + relationships, save, return counts."""
        nodes_added = self.add_entities(entities)
        edges_added = self.add_relationships(relationships)
        self.save()
        return nodes_added, edges_added

    # ── Query Methods ──────────────────────────────────────────────────────────

    def get_neighbors(
        self,
        node_id: str,
        max_hops: int = 2,
        relationship_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get all nodes reachable within max_hops from node_id.
        Returns structured context for RAG retrieval.
        """
        if not self.graph.has_node(node_id):
            return {"nodes": [], "edges": [], "paths": []}

        visited_nodes = set()
        visited_edges = []
        traversal_paths = []

        def _traverse(current: str, depth: int, path: List[str]):
            if depth > max_hops or current in visited_nodes:
                return
            visited_nodes.add(current)

            for successor in self.graph.successors(current):
                edge_data_list = self.graph.get_edge_data(current, successor)
                for key, edge_data in edge_data_list.items():
                    rel_type = edge_data.get("relationship_type", "")
                    if relationship_types and rel_type not in relationship_types:
                        continue
                    visited_edges.append({
                        "source": current,
                        "source_label": self.graph.nodes[current].get("label", current),
                        "target": successor,
                        "target_label": self.graph.nodes[successor].get("label", successor),
                        "relationship": rel_type,
                        "properties": edge_data.get("properties", {}),
                    })
                    new_path = path + [f"--[{rel_type}]-->", successor]
                    traversal_paths.append(new_path)
                    _traverse(successor, depth + 1, new_path)

            for predecessor in self.graph.predecessors(current):
                edge_data_list = self.graph.get_edge_data(predecessor, current)
                for key, edge_data in edge_data_list.items():
                    rel_type = edge_data.get("relationship_type", "")
                    if predecessor not in visited_nodes:
                        visited_edges.append({
                            "source": predecessor,
                            "source_label": self.graph.nodes[predecessor].get("label", predecessor),
                            "target": current,
                            "target_label": self.graph.nodes[current].get("label", current),
                            "relationship": rel_type,
                            "properties": edge_data.get("properties", {}),
                        })

        _traverse(node_id, 0, [node_id])

        nodes_data = [
            {
                "id": n,
                **{k: v for k, v in self.graph.nodes[n].items()},
            }
            for n in visited_nodes
            if self.graph.has_node(n)
        ]

        return {
            "nodes": nodes_data,
            "edges": visited_edges,
            "paths": [" ".join(str(s) for s in p) for p in traversal_paths[:10]],
        }

    def search_entities(
        self,
        query_terms: List[str],
        entity_types: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Fuzzy search for entities by label matching query terms.
        Returns nodes sorted by relevance score.
        """
        results = []
        query_lower = [q.lower() for q in query_terms]

        for node_id, data in self.graph.nodes(data=True):
            # Filter by entity type
            if entity_types and data.get("entity_type") not in entity_types:
                continue
            # Filter by document
            if document_ids and data.get("document_id") not in document_ids:
                continue

            label_lower = data.get("label", "").lower()
            type_lower = data.get("entity_type", "").lower()
            props_str = json.dumps(data.get("properties", {})).lower()
            source_lower = data.get("source_text", "").lower()

            combined = f"{label_lower} {type_lower} {props_str} {source_lower}"

            # Score by term overlap
            score = sum(
                1.0 for term in query_lower
                if term in combined
            )
            if score > 0:
                results.append({
                    "id": node_id,
                    "score": score,
                    **data,
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def get_graph_context_for_query(
        self,
        query_keywords: List[str],
        max_hops: int = 2,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        High-level method: given query keywords, find relevant entities
        and return their neighborhood context.
        """
        # Find seed entities matching the query
        seed_entities = self.search_entities(
            query_keywords,
            document_ids=document_ids,
            top_k=top_k,
        )

        all_context_nodes = []
        all_context_edges = []
        all_traversal_paths = []

        seen_node_ids: Set[str] = set()
        seen_edge_tuples: Set[Tuple] = set()

        for seed in seed_entities[:3]:  # Start from top 3 seeds
            neighborhood = self.get_neighbors(seed["id"], max_hops=max_hops)
            for node in neighborhood["nodes"]:
                if node["id"] not in seen_node_ids:
                    all_context_nodes.append(node)
                    seen_node_ids.add(node["id"])
            for edge in neighborhood["edges"]:
                edge_tuple = (edge["source"], edge["target"], edge["relationship"])
                if edge_tuple not in seen_edge_tuples:
                    all_context_edges.append(edge)
                    seen_edge_tuples.add(edge_tuple)
            all_traversal_paths.extend(neighborhood["paths"])

        return {
            "seed_entities": seed_entities,
            "context_nodes": all_context_nodes,
            "context_edges": all_context_edges,
            "traversal_paths": all_traversal_paths[:15],
        }

    def format_context_as_text(self, graph_context: Dict[str, Any]) -> str:
        """Convert graph context dict to readable text for LLM prompting."""
        lines = ["=== KNOWLEDGE GRAPH CONTEXT ===\n"]

        if graph_context.get("seed_entities"):
            lines.append("MATCHED ENTITIES:")
            for ent in graph_context["seed_entities"][:5]:
                props = ent.get("properties", {})
                prop_str = ", ".join(f"{k}: {v}" for k, v in props.items() if v) if props else ""
                lines.append(
                    f"  • [{ent.get('entity_type', '?')}] {ent.get('label', '?')}"
                    + (f" ({prop_str})" if prop_str else "")
                )
            lines.append("")

        if graph_context.get("context_edges"):
            lines.append("RELATIONSHIPS:")
            for edge in graph_context["context_edges"][:15]:
                lines.append(
                    f"  {edge['source_label']} --[{edge['relationship']}]--> {edge['target_label']}"
                )
            lines.append("")

        if graph_context.get("traversal_paths"):
            lines.append("TRAVERSAL PATHS:")
            for path in graph_context["traversal_paths"][:5]:
                lines.append(f"  {path}")

        return "\n".join(lines)

    # ── Analytics ──────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Return graph statistics."""
        entity_type_counts: Dict[str, int] = defaultdict(int)
        for _, data in self.graph.nodes(data=True):
            entity_type_counts[data.get("entity_type", "Unknown")] += 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "entity_types": dict(entity_type_counts),
            "documents": list(self._document_nodes.keys()),
            "is_connected": nx.is_weakly_connected(self.graph) if self.graph.number_of_nodes() > 0 else False,
        }

    def get_all_nodes_for_api(self) -> List[Dict[str, Any]]:
        """Return all nodes formatted for the frontend visualization."""
        return [
            {"id": n, **{k: v for k, v in data.items()}}
            for n, data in self.graph.nodes(data=True)
        ]

    def get_all_edges_for_api(self) -> List[Dict[str, Any]]:
        """Return all edges formatted for the frontend visualization."""
        edges = []
        for src, tgt, data in self.graph.edges(data=True):
            edges.append({
                "source": src,
                "target": tgt,
                **{k: v for k, v in data.items()},
            })
        return edges

    def remove_document(self, document_id: str) -> int:
        """Remove all nodes belonging to a document. Returns count removed."""
        nodes_to_remove = list(self._document_nodes.get(document_id, set()))
        self.graph.remove_nodes_from(nodes_to_remove)
        self._document_nodes.pop(document_id, None)
        self.save()
        return len(nodes_to_remove)


# Global singleton instance
_graph_instance: Optional[InsuranceKnowledgeGraph] = None


def get_knowledge_graph() -> InsuranceKnowledgeGraph:
    """Get or create the singleton knowledge graph instance."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = InsuranceKnowledgeGraph()
    return _graph_instance
