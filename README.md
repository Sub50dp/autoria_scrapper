# AUTO.RIA SCRAPPER
Is a tool for collecting information about cars for sale on Auto.ria.com

## Getting Started
### **Clone the Project from GitLab:** 
  
-   Copy the repository URL from GitLab.
-   Open a terminal and navigate to the directory where you want to save the project.
-   Execute the command: `git clone <repository_URL>`.

### **Run the Project in Docker using docker-compose:**
    
-   Make sure you have Docker and docker-compose installed.
-   Navigate to the directory containing the `docker-compose.yml` file.
-   Execute: 

    `docker-compose build`
    `docker-compose up`

Now your project should be up and running inside a Docker container.

### **PGAdmin:**
To view the Database you can use PGAdmin. To do this, go to http://localhost:5050/browser/.

    password for PGAdmin = 'admin'
    password for DB = '11111'

You need to create a connection to the database:

    Add New Server ->
    - General (any name)
    - Connection:
	    - Host: psql
	    - Port: 5432
	    - Maintenance database: cars_db
	    - Username: postgres
	    - Password: 11111