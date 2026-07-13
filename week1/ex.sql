--EX 1
SELECT title, author FROM books
ORDER BY title

SELECT * FROM books
WHERE year > 2000

SELECT*FROM books
WHERE genre = 'Science'
ORDER by year desc

SELECT*FROM books
ORDER BY year DESC
LIMIT 3

--EX2
SELECT*FROM rooms
WHERE status = 'vacant'

SELECT*FROM rooms
WHERE price_per_night BETWEEN 80 and 150

SELECT*FROM rooms
WHERE (type = 'double' OR type = 'suite') AND status = 'vacant'

SELECT*FROM rooms
WHERE floor >= 3 and price_per_night >= 100

SELECT*FROM rooms
ORDER BY floor asc, price_per_night desc

--ex3
SELECT*FROM trains
WHERE origin = 'Central'

SELECT*FROM trains
WHERE departure BETWEEN '08:00' and '12:00'

SELECT*FROM trains
WHERE duration_min > 90

SELECT*FROM trains
ORDER BY departure, destination

SELECT *,
    CASE
        WHEN departure < '12:00' THEN 'Morning'
        WHEN departure BETWEEN '12:00' AND '17:00' THEN 'Afternoon'
        ELSE 'Evening'
    END AS period
FROM trains;