DROP TABLE IF EXISTS Items;
DROP TABLE IF EXISTS Labels;
CREATE TABLE Items (
    date1 text NOT NULL,
    dc text NOT NULL,
    meal text NOT NULL,
    station text NOT NULL,
    dish text NOT NULL,
    vegetarian int NOT NULL,
    label text NOT NULL
);
CREATE TABLE Labels (
    id text NOT NULL,
    allergens text NOT NULL,
    ingredients text NOT NULL
);
