from cosmosDB import read_from_db

#Henter brukere fra databasen på ønsket format der hver email har et dictonary med nødvendig informasjon
def get_users():
    query = "SELECT * FROM validUsers ORDER BY validUsers._ts DESC"
    container_name = 'validUsers'
    #print(query)
    items = read_from_db(container_name, query)
    #print (items)

    users={}
    for i in items:
        users[i['email']]={ "username":i['username'],
                                "type":i['type'],
                                "password":i['password'],
                                "id":i['id']
                            }
    return users
