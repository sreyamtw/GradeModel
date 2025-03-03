# ICT_Internship
## Week1
I currently have a flask app that facilitates the following:
1. Registration
2. Login using session
3. Retrieval of student data from database
4. Exam - Only MCQ part (Hardcoding the evaluation)
5. View Result

There are Html templates supporting each routes in flask with bootstrap and css. Database is created using MySQL. The csvs were imported to the tables in the database. It contains 3 tables:
1. student_details : 150 students in total enrolled in the course
2. users : 125 students who have an account on the web application
3. scores : For storing the scores of the exam for the registered students

## Week 2 
This week is mainly focused on subjective question evaluation
* Tried to implement NLP for subjective questions
* Explored different LLMs
* Created a dataset with questions having answers ranging from 0-5 marks. About 1000 entries, some paraphrased.
* Choose T5 small and fine tuned the model
* Model needs to be improved

## Week 3 Plan
* Split the dataset and finetune again
* Try LLAMA models
* Integrate model to flask
* Modify scores table to add in scores
* Try to build code evaluation part
