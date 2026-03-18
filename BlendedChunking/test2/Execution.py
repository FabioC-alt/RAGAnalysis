from neo4j import GraphDatabase
import re

# ... [Your stream_relationships function here] ...

URI = "neo4j://localhost:7687"
NEO4J_AUTH = ("neo4j", "testpassword")
filename = "oran.txt"


def extract_structured_text(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Split the text into blocks separated by at least one empty line
        raw_blocks = content.split('\n\n')

        structured_data = []

        for block in raw_blocks:
            # Clean the block and split into internal lines
            lines = [line.strip() for line in block.split('\n') if line.strip()]

            if not lines:
                continue

            # Apply your redefined rules
            if len(lines) == 1:
                structured_data.append({
                    "type": "Title",
                    "text": lines[0]
                })
            else:
                structured_data.append({
                    "type": "Paragraph",
                    "text": " ".join(lines)  # Join lines into a single string
                })

        return structured_data

    except FileNotFoundError:
        return "Error: File not found."

# Execution
data = extract_structured_text(filename)

# Displaying results
for item in data:
    print(f"[{item['type'].upper()}]: {item['text'][:70]}...")

import re

def stream_relationships(large_text):
    # This pattern specifically targets the Relationship Format:
    # It looks for: #Number [Subject] -> [Verb] -> [Object]
    # We use \s* to handle any inconsistent spacing around the arrows.
    rel_pattern = re.compile(r"#(\d+)\s+(.*?)\s*->\s*(.*?)\s*->\s*(.*)")

    # Splitting by newline to simulate line-by-line reading
    for line in large_text.splitlines():
        clean_line = line.strip()

        # We only care about lines that match our specific relationship pattern
        match = rel_pattern.search(clean_line)
        if match:
            yield {
                "id": int(match.group(1)),
                "subject": match.group(2).strip(),
                "verb": match.group(3).replace(" ",""),
                "object": match.group(4).strip()
            }
import ollama
import json

def self_discover_and_extract(title, paragraphs, entity_types, predicates):
    sample_text = f"Title: {title}\n\n" + "\n".join(paragraphs[:3])

    discovery_prompt = f"""Perform Named Entity Recognition (NER) and extract knowledge graph triplets from the text. NER identifies named entities of given entity types, and triple extraction identifies relationships between entities using specified predicates.

        **Entity Types:**
        {json.dumps(entity_types)}

        **Predicates:**
        {json.dumps(predicates)}

        **Text:**
        {sample_text}

        **Example Output:**
            "entities": [{{ "text": "Google", "type": "ORGANIZATION" }}],
            "triplets": [{{ "subject": "Google", "predicate": "founded_in", "object": "USA" }}]
        """

    discovery_prompt=f"""
                        Prompt for extracting entities: Extract key entities from the given
                        text. Extracted entities are nouns, verbs, or adjectives,
                        particularly regarding sentiment. This is for an extraction
                        task, please be thorough and accurate to the reference text.

                        Prompt for extracting relations: Extract subject-predicate-object
                        triples from the assistant message. A predicate (1-3
                        words) defines the relationship between the subject and
                        object. Relationship may be fact or sentiment based on
                        assistant’s message. Subject and object are entities.
                        Entities provided are from the assistant message and
                        prior conversation history, though you may not need all of
                        them. This is for an extraction task, please be thorough,
                        accurate, and faithful to the reference text

                        In the end represent all the relationships with this format, do not add text:

                        *Relationship Format:*

                        #[Number] Entity -> Predicate -> Entity

                        {sample_text}
                        """

    # Remove the redundant .format() call — the f-string already handled substitution
    discovery_response = ollama.chat(model='llama3:8b', messages=[
        {'role': 'user', 'content': discovery_prompt}
    ])
    return discovery_response['message']['content']

# Usage
# schema, triplets = self_discover_and_extract(my_title, my_paragraphs)for p in range(len(data)-1):

for p in range(len(data)-1):
    current_val =data[p]
    next_val = data[p+1]

    if current_val['type'] == 'Title' and next_val['type'] == 'Paragraph':
        my_title = current_val['text']
        my_paragraphs = [next_val['text']]



        entity_types = ["Person", "Organization", "Object", "Subject"]
        predicates = ["related_to", "located_in", "participated_in"]

        data_n = self_discover_and_extract(my_title, my_paragraphs, entity_types, predicates)
        extracted_triplets = list(stream_relationships(data_n))
        # 3. Print the actual parsed dictionaries
        print(f"--- Results for: {my_title} ---")
        for triplet in extracted_triplets:
            print(triplet)

import ollama
import json

def self_discover_and_extract(title, paragraphs, entity_types, predicates):
    sample_text = f"Title: {title}\n\n" + "\n".join(paragraphs[:3])

    discovery_prompt = f"""Perform Named Entity Recognition (NER) and extract knowledge graph triplets from the text. NER identifies named entities of given entity types, and triple extraction identifies relationships between entities using specified predicates.

        **Entity Types:**
        {json.dumps(entity_types)}

        **Predicates:**
        {json.dumps(predicates)}

        **Text:**
        {sample_text}

        **Example Output:**
            "entities": [{{ "text": "Google", "type": "ORGANIZATION" }}],
            "triplets": [{{ "subject": "Google", "predicate": "founded_in", "object": "USA" }}]
        """

    discovery_prompt=f""" 
                        Prompt for extracting entities: Extract key entities from the given
                        text. Extracted entities are nouns, verbs, or adjectives,
                        particularly regarding sentiment. This is for an extraction
                        task, please be thorough and accurate to the reference text.

                        Prompt for extracting relations: Extract subject-predicate-object
                        triples from the assistant message. A predicate (1-3
                        words) defines the relationship between the subject and
                        object. Relationship may be fact or sentiment based on
                        assistant’s message. Subject and object are entities.
                        Entities provided are from the assistant message and
                        prior conversation history, though you may not need all of
                        them. This is for an extraction task, please be thorough,
                        accurate, and faithful to the reference text

                        In the end represent all the relationships with this format, do not add text:
                        
                        *Relationship Format:*

                        #[Number] Entity -> Predicate -> Entity

                        {sample_text}
                        """

    # Remove the redundant .format() call — the f-string already handled substitution
    discovery_response = ollama.chat(model='llama3:8b', messages=[
        {'role': 'user', 'content': discovery_prompt}
    ])
    return discovery_response['message']['content']

# Usage
# schema, triplets = self_discover_and_extract(my_title, my_paragraphs)for p in range(len(data)-1):

for p in range(len(data)-1):
    current_val =data[p]
    next_val = data[p+1]

    if current_val['type'] == 'Title' and next_val['type'] == 'Paragraph':
        my_title = current_val['text']
        my_paragraphs = [next_val['text']]

        

        entity_types = ["Person", "Organization", "Object", "Subject"]
        predicates = ["related_to", "located_in", "participated_in"]

        data_n = self_discover_and_extract(my_title, my_paragraphs, entity_types, predicates)
        extracted_triplets = list(stream_relationships(data_n))
        # 3. Print the actual parsed dictionaries
        print(f"--- Results for: {my_title} ---")
        for triplet in extracted_triplets:
            print(triplet)

def upload_triplets(driver, triplets):
    with driver.session() as session:
        for triplet in triplets:
            rel_type = re.sub(r'[^a-zA-Z0-9_]', '', triplet['verb'].replace(" ", "_").upper())
            
            # Use an f-string ONLY for the relationship type, 
            # use parameters ($sub, $obj) for the actual data.
            query = (
                f"MERGE (s:Entity {{name: $sub}}) "
                f"MERGE (o:Entity {{name: $obj}}) "
                f"MERGE (s)-[:{rel_type}]->(o)"
            )
            session.run(query, sub=triplet['subject'], obj=triplet['object'])


# Integration with your Ollama loop
with GraphDatabase.driver(URI, auth=NEO4J_AUTH) as driver:
    driver.verify_connectivity()
    
    for p in range(len(data)-1):
        # ... [Your Ollama extraction logic] ...
        data_n = self_discover_and_extract(my_title, my_paragraphs, entity_types, predicates)
        
        # Parse the text into dictionaries
        triplets = list(stream_relationships(data_n))
        
        # Upload to Neo4j
        if triplets:
            upload_triplets(driver, triplets)
        else:
            print("No relationships parsed; skipping Neo4j upload.")
            continue
        print(f"Uploaded {len(triplets)} relationships to Neo4j.")

