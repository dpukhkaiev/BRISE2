var db = connect("mongodb://localhost/test_db");

db.createRole(
    {
        role: "user",
        privileges: [
            {
              actions: [ "find", "update", "insert" ],
              resource: { db: "test_db", collection: "" }
            }
          ],
        roles: [  ]
    }
)

db.createUser(
    {
        user: "user",
        pwd: "test111",
        roles: [ { role: "user", db: "test_db" } ]
    }
)
