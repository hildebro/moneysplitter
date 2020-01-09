-- Rework items and purchases to work with the new purchase interface

-- Remove unfinished purchases
DELETE
FROM purchases
WHERE price IS NULL
   OR active = True;

-- Add not-null constraint, because it became a constructor parameter
ALTER TABLE purchases
    ALTER COLUMN price SET NOT NULL;

-- Remove columns that were used for buffered purchases
ALTER TABLE items
    DROP COLUMN purchase_order;
ALTER TABLE purchases
    DROP COLUMN active;