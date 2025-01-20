-- Create the User table
CREATE TABLE User (
                      id INT AUTO_INCREMENT PRIMARY KEY,
                      username VARCHAR(80) NOT NULL UNIQUE,
                      email VARCHAR(120) NOT NULL UNIQUE,
                      password VARCHAR(120) NOT NULL
);

-- Create the StudyGroup table
CREATE TABLE StudyGroup (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            name VARCHAR(80) NOT NULL UNIQUE
);

-- Create the user_studygroup association table
CREATE TABLE user_studygroup (
                                 user_id INT,
                                 studygroup_id INT,
                                 PRIMARY KEY (user_id, studygroup_id),
                                 FOREIGN KEY (user_id) REFERENCES User(id),
                                 FOREIGN KEY (studygroup_id) REFERENCES StudyGroup(id)
);
