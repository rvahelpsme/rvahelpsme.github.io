import traceback

def search_and_prune_directory(supabase_client, classifier_data: dict, locked_lang: str) -> list:
    try:
        response = supabase_client.table('resources').select('*').eq('is_active', True).execute()
        directory = response.data
    except Exception as e:
        print(f"Directory Fetch Error: {repr(e)}")
        return []

    if not directory:
        return []

    broad = [b.lower() for b in classifier_data.get('broad_buckets', [])]
    specific = [s.lower() for s in classifier_data.get('specific_intents', [])]
    all_query_intents = set(broad + specific)

    filtered_directory = []
    lang_columns = {'description_es', 'description_ar', 'description_fa', 'description_ps', 'description_pt', 'description_ne', 'description_my'}
    lang_columns_to_remove = {col for col in lang_columns if locked_lang not in col}
    base_keys_to_remove = {'id', 'provider_hash', 'created_at', 'last_updated'} | lang_columns_to_remove

    for resource in directory:
        db_tags = resource.get('intent_categories', [])
        if not isinstance(db_tags, list):
            db_tags = [db_tags]

        db_tags_lower = {str(t).lower() for t in db_tags}

        if all_query_intents and not all_query_intents.intersection(db_tags_lower):
            continue

        for key in base_keys_to_remove:
            resource.pop(key, None)

        filtered_directory.append(resource)

    return filtered_directory[:5]