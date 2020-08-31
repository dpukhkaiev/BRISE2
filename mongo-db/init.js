var db = connect("mongodb://localhost/BRISE_db");

db.createRole(
    {
        role: "user",
        privileges: [
            {
              actions: [ "find", "update", "insert" ],
              resource: { db: "BRISE_db", collection: "" }
            }
          ],
        roles: [  ]
    }
)

db.createUser(
    {
        user: "user",
        pwd: "5V5Scp1E",
        roles: [ { role: "user", db: "BRISE_db" } ]
    }
)
