# A-MEM Paper Appendix B.1 - Note Construction
NOTE_CONSTRUCTION_PROMPT = """
Generate a structured analysis of the following content by:
1. Identifying the most salient keywords (focus on nouns, verbs, and key concepts)
2. Extracting core themes and contextual elements
3. Creating relevant categorical tags

Format the response as a JSON object:
{
    "keywords": ["keyword1", "keyword2", ...], // Order from most to least important. At least 3.
    "context": "One sentence summarizing main topic, key arguments, and purpose.",
    "tags": ["tag1", "tag2", ...] // Broad categories/themes. At least 3.
}

Content for analysis:
{content}
"""

# A-MEM Paper Appendix B.2 - Link Generation (Simplified for JSON output consistency)
LINK_GENERATION_PROMPT = """
You are an AI memory evolution agent. Analyze the new memory note and its nearest neighbors to determine meaningful connections.

New Memory:
Context: {new_context}
Content: {new_content}
Keywords: {new_keywords}

Nearest Neighbors:
{neighbors_info}

Determine if the new memory should be explicitly linked to any of the neighbors based on shared themes, causality, or contradiction.
Return a JSON object:
{
    "linked_memory_ids": ["id_1", "id_2"] // List of IDs from neighbors that should be linked. Empty list if none.
}
"""

# A-MEM Paper Appendix B.3 - Memory Evolution
MEMORY_EVOLUTION_PROMPT = """
You are an AI memory evolution agent. Analyze the new memory and its neighbors. 
Your goal is to "evolve" the neighbors - update their tags or context if the new information changes our understanding of them (e.g., adding a new perspective).

New Memory: {new_content}
Neighbors:
{neighbors_info}

Return a JSON object with updates for neighbors (only include if updates are needed):
{
    "updates": [
        {
            "id": "neighbor_id",
            "new_context": "Updated context summary...",
            "new_tags": ["tag1", "tag2", "new_tag"]
        }
    ]
}
"""