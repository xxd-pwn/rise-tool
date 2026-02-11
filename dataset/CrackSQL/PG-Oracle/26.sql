SELECT "t1"."fastestlap" FROM "results" AS "t1" INNER JOIN "races" AS "t2" ON "t1"."raceid" = "t2"."raceid" WHERE "t2"."year" = 2009 AND "t1"."time" LIKE '_:%:__.___'
