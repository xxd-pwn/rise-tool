SELECT "text" FROM "comments" WHERE "postid" IN ( SELECT "id" FROM "posts" WHERE "viewcount" BETWEEN 100 AND 150 ) ORDER BY "score" DESC NULLS LAST LIMIT 1
