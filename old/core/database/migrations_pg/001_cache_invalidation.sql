-- Cache invalidation via LISTEN/NOTIFY for Postgres
-- Safe, idempotent-ish: wrap in DO blocks to avoid errors on re-apply

-- Function to send NOTIFY with JSON payload
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE p.proname = 'tg_notify_cards_v2' AND n.nspname = 'public'
  ) THEN
    CREATE FUNCTION public.tg_notify_cards_v2() RETURNS trigger AS $$
    DECLARE
      v_partner_id integer;
      v_category_id integer;
    BEGIN
      IF (TG_OP = 'DELETE') THEN
        v_partner_id := OLD.partner_id;
        v_category_id := OLD.category_id;
      ELSE
        v_partner_id := NEW.partner_id;
        v_category_id := NEW.category_id;
      END IF;

      -- Notify catalog caches (city_id unknown here -> use null; consumer treats as '*')
      PERFORM pg_notify('cache_invalidation', json_build_object(
        'type', 'catalog',
        'city_id', NULL,
        'category_id', v_category_id
      )::text);

      -- Notify partner cabinet caches
      PERFORM pg_notify('cache_invalidation', json_build_object(
        'type', 'partner_cab',
        'partner_profile_id', v_partner_id,
        'category_id', v_category_id
      )::text);

      RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;
  END IF;
END $$;

-- Create trigger on cards_v2 for INSERT/UPDATE/DELETE
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'tr_cards_v2_cache_invalidation'
  ) THEN
    CREATE TRIGGER tr_cards_v2_cache_invalidation
    AFTER INSERT OR UPDATE OR DELETE ON public.cards_v2
    FOR EACH ROW EXECUTE FUNCTION public.tg_notify_cards_v2();
  END IF;
END $$;
