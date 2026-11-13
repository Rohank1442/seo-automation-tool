-- Read-only preflight: inspect project/cluster key types and their foreign keys.
SELECT
    c.table_name,
    c.column_name,
    c.data_type,
    c.udt_name AS postgres_type,
    foreign_keys.referenced_table,
    foreign_keys.referenced_column,
    foreign_keys.delete_rule
FROM information_schema.columns AS c
LEFT JOIN (
    SELECT
        kcu.table_schema,
        kcu.table_name,
        kcu.column_name,
        ccu.table_name AS referenced_table,
        ccu.column_name AS referenced_column,
        rc.delete_rule
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON kcu.constraint_schema = tc.constraint_schema
        AND kcu.constraint_name = tc.constraint_name
        AND kcu.table_schema = tc.table_schema
        AND kcu.table_name = tc.table_name
    JOIN information_schema.referential_constraints AS rc
        ON rc.constraint_catalog = tc.constraint_catalog
        AND rc.constraint_schema = tc.constraint_schema
        AND rc.constraint_name = tc.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_schema = tc.constraint_schema
        AND ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
) AS foreign_keys
    ON foreign_keys.table_schema = c.table_schema
    AND foreign_keys.table_name = c.table_name
    AND foreign_keys.column_name = c.column_name
WHERE c.table_schema = 'public'
    AND (
        (c.table_name = 'projects' AND c.column_name = 'id')
        OR (c.table_name = 'clusters' AND c.column_name IN ('id', 'project_id'))
        OR (c.table_name = 'keywords' AND c.column_name = 'cluster_id')
        OR (c.table_name IN (
            'project_clarifications',
            'pipeline_runs',
            'site_architectures',
            'generated_pages',
            'page_indexing_metrics',
            'monitoring_alerts'
        ) AND c.column_name IN ('id', 'project_id'))
    )
ORDER BY c.table_name, c.column_name;
