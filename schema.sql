CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE medicines (
    id bigint PRIMARY KEY,
    sku_id bigint,
    name text NOT NULL,
    search_name text,  -- new column for normalized search
    manufacturer_name text,
    marketer_name text,
    type text,
    price numeric,
    pack_size_label text,
    short_composition text,
    is_discontinued boolean,
    available boolean,
    slug text,
    image_url text,
    tsv tsvector -- materialized tsvector for full-text search
);

-- Functional index for case-insensitive prefix searches (fast for `col ILIKE 'prefix%'`)
CREATE INDEX idx_medicines_lower_name_varchar_pattern ON medicines (lower(name) varchar_pattern_ops);

-- Trigram GIN index for substring and fuzzy search
CREATE INDEX idx_medicines_name_trgm ON medicines USING gin (name gin_trgm_ops);

-- Trigram indexes for manufacturer and composition
CREATE INDEX idx_medicines_manufacturer_trgm ON medicines USING gin (manufacturer_name gin_trgm_ops);
CREATE INDEX idx_medicines_composition_trgm ON medicines USING gin (short_composition gin_trgm_ops);

-- Full-text tsvector column index
CREATE INDEX idx_medicines_tsv_gin ON medicines USING gin (tsv);

-- Optional: index to speed up similarity ordering
CREATE INDEX idx_medicines_name_lower ON medicines (lower(name));

-- Trigger function to keep tsvector and search_name up-to-date 
CREATE FUNCTION medicines_tsv_trigger() RETURNS trigger AS $$
BEGIN
    -- Normalize name by removing dosage info for search
    NEW.search_name := regexp_replace(NEW.name, '\d+mg.*$', '', 'i');

    -- Build tsvector
    NEW.tsv :=
        setweight(to_tsvector('english', coalesce(NEW.name,'')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.search_name,'')), 'A') ||  -- include search_name
        setweight(to_tsvector('english', coalesce(NEW.short_composition,'')), 'B') ||
        setweight(to_tsvector('english', coalesce(NEW.manufacturer_name,'')), 'C');

    RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER tsv_update
BEFORE INSERT OR UPDATE ON medicines
FOR EACH ROW EXECUTE PROCEDURE medicines_tsv_trigger();
