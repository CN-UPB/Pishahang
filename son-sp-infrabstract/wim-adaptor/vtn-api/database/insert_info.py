from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker

from sqlalchemy_declaritive import Base, Connectivity

engine = create_engine('sqlite:///wim_info.db')
# bind the engine to the metadata of the base 
Base.metadata.bind = engine 
DBSession = sessionmaker(bind=engine)
# dbsession establishes 'conversations' with the database 
session = DBSession()
#insert data on the table(s)
print "Welcome to the WIM-info database helper"

while True:
	print "Enter new database entry "
	segment = raw_input("Enter Segment: ")
	bridge_name = raw_input("Enter Vbridge name: ")
	port_id = raw_input("Enter port_id: ")
	location = raw_input("Enter location: ")
	print("You provided the following info: ")
	print("Segment: "+segment)
	print ("Bridge name: " +bridge_name)
	print ("Port ID: "+port_id)
	print ("Location: "+location)
	var = raw_input("If dissagree type 'q' ")
	if var == 'q':
		break
	new_conn = Connectivity(segment=segment, bridge_name=bridge_name,port_id=port_id,location=location)
	session.add(new_conn)
	session.commit()
	var = raw_input("You want to add more? (y/q)")
	if var == 'q':
		break



