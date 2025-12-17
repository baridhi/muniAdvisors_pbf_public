import ollama
from thefuzz import process
from thefuzz import fuzz
import pandas as pd
import time
import re

# --- Configuration ---
OLLAMA_MODEL = "mistral"  # Ensure you have 'mistral' pulled in Ollama
FUZZY_MATCH_THRESHOLD = 75 # Initial fuzzy matching threshold (0-100)
LLM_CONFIDENCE_THRESHOLD = 0.8 # Threshold for LLM's confidence score (0.0-1.0)
MAX_LLM_CANDIDATES = 5 # How many top fuzzy matches to send to the LLM for re-evaluation

# --- Sample Data (Replace with your actual table data) ---
table1_entries = [
    {"id": "T1_001", "name": "John Doe"},
    {"id": "T1_002", "name": "Jane Smith"},
    {"id": "T1_003", "name": "Michael Johnson"},
    {"id": "T1_004", "name": "Emily White"},
    {"id": "T1_005", "name": "Christopher Brown"},
    {"id": "T1_006", "name": "Maria Garcia"},
    {"id": "T1_007", "name": "David Lee"},
    {"id": "T1_008", "name": "Sarah Miller"},
    {"id": "T1_009", "name": "William Davis"},
    {"id": "T1_010", "name": "Olivia Wilson"},
    {"id": "T1_011", "name": "PATRICK CAPITAL MARKETS, LLC"}, # Example for testing bad match
    {"id": "T1_012", "name": "GOOGLE INC."},
    {"id": "T1_013", "name": "Apple Corporation"},
]

table2_entries = [
    {"id": "T2_A", "name": "Jon Do"},
    {"id": "T2_B", "name": "Jane Smythe"},
    {"id": "T2_C", "name": "Micheal Johnsons"},
    {"id": "T2_D", "name": "Emly Whyte"},
    {"id": "T2_E", "name": "Chrisopher Brouwn"},
    {"id": "T2_F", "name": "Marya Garsia"},
    {"id": "T2_G", "name": "Dave Lee"},
    {"id": "T2_H", "name": "Sara Miler"},
    {"id": "T2_I", "name": "Willm Davies"},
    {"id": "T2_J", "name": "Oliva Wlson"},
    {"id": "T2_K", "name": "MBS CAPITAL MARKETS LLC"}, # Example for testing bad match
    {"id": "T2_L", "name": "Alphabet Inc."},
    {"id": "T2_M", "name": "Apple Co."},
    {"id": "T2_X", "name": "Non-matching Name X"} # An example of a name that shouldn't match
]

print("--- Starting Crosswalk Process ---")
print(f"Table 1 entries: {len(table1_entries)}")
print(f"Table 2 entries: {len(table2_entries)}\n")

# --- Helper Function for Name Normalization ---
def normalize_name(name: str) -> str:
    """
    Normalizes a string by converting to lowercase, removing common business suffixes,
    and extra spaces.
    """
    normalized = name.lower()
    # Remove common legal/business suffixes and punctuation
    suffixes = [
        r'\s*llc\.?', r'\s*inc\.?', r'\s*co\.?', r'\s*corp\.?',
        r'\s*ltd\.?', r'\s*group\.?', r'\s*capital\.?', r'\s*markets\.?',
        r'\s*corporation\.?'
    ]
    for suffix in suffixes:
        normalized = re.sub(suffix, '', normalized)
    
    # Remove any non-alphanumeric characters except spaces
    normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
    # Replace multiple spaces with a single space and strip leading/trailing spaces
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

# --- Ollama Interaction Function ---
def get_llm_match_score(name1: str, name2: str) -> float:
    """
    Uses the Ollama LLM (Mistral) to determine a similarity score between two names.
    The LLM is asked to output a JSON object with a 'match_score'.
    The prompt is designed to make the LLM act more like a human agent.
    """
    prompt = f"""You are an expert at identifying similar entity names, even with spelling errors or slight variations.
    Your goal is to determine if two names refer to the *same underlying entity*.

    Rate their similarity on a scale from 0.0 to 1.0, where:
    - 1.0 is a perfect match (e.g., "Google Inc." and "Alphabet Inc." if you know they are the same, or "John Doe" and "John Doe").
    - 0.0 is no similarity.

    Consider the following:
    - Focus primarily on the *unique identifying words* or core parts of the names.
    - Common descriptive terms or legal suffixes (e.g., "LLC", "Capital Markets", "Group", "Corp") should be given less weight if the primary names are different.
    - Account for common spelling mistakes (e.g., "Jon Do" vs "John Doe") and variations.
    - If the core entities are clearly distinct, even if they share common industry terms, the score should be low.

    Return your answer as a JSON object with a single key 'match_score'.
    Example: {{ "match_score": 0.95 }}

    Name 1: "{name1}"
    Name 2: "{name2}"
    """
    
    # Implement exponential backoff for API calls
    retries = 3
    for i in range(retries):
        try:
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.1}, # Keep temperature low for deterministic output
                format='json' # Request JSON output
            )
            # Parse the JSON response
            import json
            if 'message' in response and 'content' in response['message']:
                content = response['message']['content']
                try:
                    score_data = json.loads(content)
                    return float(score_data.get('match_score', 0.0))
                except json.JSONDecodeError:
                    print(f"Warning: LLM did not return valid JSON for '{name1}' vs '{name2}'. Response: {content}")
                    return 0.0 # Default to no match if JSON is invalid
            else:
                print(f"Warning: Unexpected LLM response structure for '{name1}' vs '{name2}'. Response: {response}")
                return 0.0
        except ollama.ResponseError as e:
            if e.status_code == 404:
                print(f"Error: Model '{OLLAMA_MODEL}' not found. Please pull it using 'ollama pull {OLLAMA_MODEL}'.")
                return 0.0
            elif e.status_code == 503 and i < retries - 1: # Service Unavailable, retry
                wait_time = (2 ** i) # Exponential backoff
                print(f"LLM call failed (status 503), retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Error communicating with Ollama: {e}")
                return 0.0
        except Exception as e:
            print(f"An unexpected error occurred during LLM call: {e}")
            return 0.0
    return 0.0 # Return 0 if all retries fail


# --- Perform Crosswalk ---
crosswalk_results = []

# Extract names for fuzzy matching. Use normalized names for better initial candidate generation.
table2_names_normalized = [normalize_name(entry["name"]) for entry in table2_entries]
# Map normalized name back to original name and ID for results
table2_normalized_to_original_map = {normalize_name(entry["name"]): {"original_name": entry["name"], "id": entry["id"]} for entry in table2_entries}


for entry1 in table1_entries:
    original_name1 = entry1["name"]
    id1 = entry1["id"]
    name1_normalized = normalize_name(original_name1)

    best_fuzzy_match_normalized_name = None
    best_fuzzy_match_original_name = None
    best_fuzzy_match_id = None
    best_fuzzy_score = -1

    # Step 1: Initial fuzzy matching to get top candidates using normalized names
    # We pass the normalized names for the fuzzy matching process
    fuzzy_matches = process.extract(name1_normalized, table2_names_normalized, scorer=fuzz.token_sort_ratio, limit=MAX_LLM_CANDIDATES)

    llm_determined_match_original_name = None
    llm_determined_match_id = None
    highest_llm_score = 0.0

    if not fuzzy_matches:
        print(f"No fuzzy matches found for '{original_name1}' (ID: {id1}).")
        crosswalk_results.append({
            "Table1_ID": id1,
            "Table1_Name": original_name1,
            "Table2_ID_Match": None,
            "Table2_Name_Match": None,
            "Match_Method": "No Match",
            "Fuzzy_Score": None,
            "LLM_Score": None
        })
        continue

    # Step 2: Re-evaluate top fuzzy matches using LLM for semantic understanding
    for candidate_normalized_name, fuzzy_score in fuzzy_matches:
        if fuzzy_score >= FUZZY_MATCH_THRESHOLD:
            # Get original name from the map for LLM evaluation, as LLM might benefit from original context
            candidate_original_info = table2_normalized_to_original_map.get(candidate_normalized_name)
            if candidate_original_info:
                candidate_original_name = candidate_original_info["original_name"]
                candidate_id = candidate_original_info["id"]

                # Pass original names to LLM for richer context
                llm_score = get_llm_match_score(original_name1, candidate_original_name)
                
                if llm_score > highest_llm_score:
                    highest_llm_score = llm_score
                    llm_determined_match_original_name = candidate_original_name
                    llm_determined_match_id = candidate_id
                    best_fuzzy_match_original_name = candidate_original_name # Store the fuzzy match that led to the best LLM score
                    best_fuzzy_match_id = candidate_id
                    best_fuzzy_score = fuzzy_score # Store the fuzzy score for this best candidate

    if llm_determined_match_original_name and highest_llm_score >= LLM_CONFIDENCE_THRESHOLD:
        crosswalk_results.append({
            "Table1_ID": id1,
            "Table1_Name": original_name1,
            "Table2_ID_Match": llm_determined_match_id,
            "Table2_Name_Match": llm_determined_match_original_name,
            "Match_Method": "LLM Refined Fuzzy",
            "Fuzzy_Score": best_fuzzy_score,
            "LLM_Score": highest_llm_score
        })
    else:
        # If LLM didn't confirm or score too low, try to use the best fuzzy match if it's strong
        # This fallback also uses the original name and ID that corresponded to the best fuzzy match
        if best_fuzzy_match_original_name and best_fuzzy_score >= FUZZY_MATCH_THRESHOLD:
            crosswalk_results.append({
                "Table1_ID": id1,
                "Table1_Name": original_name1,
                "Table2_ID_Match": best_fuzzy_match_id,
                "Table2_Name_Match": best_fuzzy_match_original_name,
                "Match_Method": "Fuzzy Only (LLM low confidence)",
                "Fuzzy_Score": best_fuzzy_score,
                "LLM_Score": highest_llm_score
            })
        else:
            crosswalk_results.append({
                "Table1_ID": id1,
                "Table1_Name": original_name1,
                "Table2_ID_Match": None,
                "Table2_Name_Match": None,
                "Match_Method": "No Match",
                "Fuzzy_Score": None,
                "LLM_Score": None
            })

# --- Display Results ---
results_df = pd.DataFrame(crosswalk_results)
print("\n--- Crosswalk Results ---")
print(results_df.to_string())

print("\n--- Summary ---")
matched_count = results_df['Table2_Name_Match'].count()
print(f"Total entries in Table 1: {len(table1_entries)}")
print(f"Total matched entries: {matched_count}")
print(f"Unmatched entries: {len(table1_entries) - matched_count}")
