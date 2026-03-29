def search_and_prune_directory(supabase_client, classifier_data: dict, locked_lang: str) -> list:
    try:
        response = supabase_client.table('resources').select('*').eq('is_active', True).execute()
        directory = response.data
    except Exception as e:
        print(f"Directory Fetch Error: {repr(e)}")
        return []

    if not directory: return []

    broad = [b.lower() for b in classifier_data.get('broad_buckets', [])]
    specific = [s.lower() for s in classifier_data.get('specific_intents', [])]
    user_demographics = set([d.lower() for d in classifier_data.get('user_demographics', [])])

    scored_resources = []
    lang_columns = {'description_es', 'description_ar', 'description_fa', 'description_ps', 'description_pt',
                    'description_ne', 'description_my'}
    lang_columns_to_remove = {col for col in lang_columns if locked_lang not in col}
    base_keys_to_remove = {'id', 'provider_hash', 'created_at', 'last_updated'} | lang_columns_to_remove

    for resource in directory:
        db_tags = resource.get('intent_categories', [])
        if not isinstance(db_tags, list): db_tags = [db_tags]
        db_tags_lower = {str(t).lower().strip() for t in db_tags}

        # RELEVANCE SCORING
        score = 0
        for intent in specific:
            if intent in db_tags_lower: score += 10
        for bucket in broad:
            if bucket in db_tags_lower: score += 1

        if score == 0: continue

        # DEMOGRAPHIC FILTERING
        db_pops = resource.get('target_populations', [])
        if not isinstance(db_pops, list): db_pops = [db_pops]
        db_pops_lower = {str(p).lower().strip() for p in db_pops}

        is_general = any(pop in db_pops_lower for pop in ['everyone', 'general public', 'all', 'adults', 'individuals'])
        if not is_general:
            if not user_demographics.intersection(db_pops_lower):
                continue  # Skip resource if demographic doesn't explicitly match

        for key in base_keys_to_remove:
            resource.pop(key, None)

        scored_resources.append((score, resource))

    # Sort by highest score first, return top 10 for Gemini to choose from
    scored_resources.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in scored_resources[:10]]