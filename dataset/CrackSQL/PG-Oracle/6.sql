SELECT "t2"."url" FROM "constructorresults" AS "t1" INNER JOIN "constructors" AS "t2" ON "t2"."constructorid" = "t1"."constructorid" WHERE "t1"."raceid" = 9 ORDER BY "t1"."points" DESC NULLS LAST 
