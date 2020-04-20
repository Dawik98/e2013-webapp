from cosmosDB import read_from_db

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
    #print(users)
    #user=users["kristoffer.hovland@hotmail.com"]["password"]
    #print(user)
    return users
