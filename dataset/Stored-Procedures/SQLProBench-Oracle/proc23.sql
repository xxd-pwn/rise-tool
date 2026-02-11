CREATE or replace PROCEDURE CreateRandomString (randomString IN OUT VARCHAR2)
as
  stringLength INT :=16;
  chars VARCHAR(200);
begin
  chars:= 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  randomString := '';
  WHILE LENGTH(randomString) < stringLength loop
    randomString := randomString || 'a';
  END LOOP;
END;