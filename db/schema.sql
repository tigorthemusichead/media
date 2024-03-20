DROP TABLE IF EXISTS users;

CREATE TABLE users (
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" TEXT PRIMARY KEY NOT NULL,
    "password_hash" TEXT,
    "jwt" TEXT
);

DROP TABLE IF EXISTS results;
CREATE TABLE results (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "filename" TEXT NOT NULL,
    "username" TEXT NOT NULL,
    FOREIGN KEY ("username") REFERENCES users ("name")
);