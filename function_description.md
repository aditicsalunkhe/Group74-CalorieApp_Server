login()
- This function is used for login by the user
- Using email ID and passoword is validated and the user is directed to home

logout()
- This function is used for logout by the user
- logout() function just clears the session

forgot()
- This function enables the user to send a password rest link to their email.

register()
- This function is used for registering new users
- Details of new users are stored in the database and the user is redirected to login page

homePage()
- This function renders the home page

send_email()
- This function is used to send an email to user's friends containing calorie history of user
- The user will fill a textarea with their friends email IDs (comma seperated if multiple)

calories()
- This function will add calories consumed/burned for the data selected.

profile()
- This function is used to store/display user's profile details such as height, weight and goal weight

history()
- This function displays user's historical calorie consumption and burnout at date level

friends()
- This function allows user to accept friend requests and display all friends

yoga()/swim()/abbs()/belly()/core()/gym()/walk()/dance()/hrx()
- This function allows user to enroll in different plans

remove_status()
- This function allows the user to un-enroll from the list of plans they enrolled in earlier

my_enrolled_workouts()
- This function is used to fetch the list of workouts the user is currently enrolled in

get_burnbot()
- This function is used to get the respons of the burnbot based on the user query.

edit_profile()
- This function is used to change the user profile data such as height, weight and goal weight

easy_enroll()
- This function quickly enrolls a user in the given workout without having to go through all the details of the workout.

core()
- This function displays the belly.html template


