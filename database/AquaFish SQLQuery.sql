-- User table --

CREATE TABLE Users(
    UID int NOT NULL identity(1,1) Primary Key ,
    name varchar(255) NOT NULL,
	email varchar(255),
	password varchar(255),
	status varchar(255),
);
Select * from Users
Delete from Users
Drop table Users

-- Contact Us --

CREATE TABLE Contacts (
    Con_id int NOT NULL identity(1,1) Primary Key ,
    name varchar(255) NOT NULL,
	email varchar(255),
	message nvarchar(MAX),
);
Select * from Contacts
Delete from Contacts
Drop table Contacts


-- Fish Details --
CREATE TABLE FishDetails (
    Fish_id int NOT NULL identity(1,1) Primary Key ,
    Fish_Name varchar(255) NOT NULL,
	
	Description nvarchar(MAX)

);

Select * from FishDetails
Delete from FishDetails where Fish_id=24 
Drop table FishDetails
		