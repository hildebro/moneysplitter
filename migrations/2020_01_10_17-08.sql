-- Remove unique constraint of checklist_id + name on items. No longer necessary for functionality

ALTER TABLE items
    DROP CONSTRAINT items_name_checklist_id_key;