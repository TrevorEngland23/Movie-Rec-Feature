# XBC Recommendation Engine  

This repository contains two main projects:  

- **Azure-Functions**: Backend Azure Functions app  
- **XBC-Recommendation-Engine**: Flask front-end application  

This project is a 3 layer application that takes advantage of microservices. Both project directories have a Dockerfile that was used to create an image of the respective project. The Azure Functions were deployed to the cloud on Elastic Premium tier, hosted on Linux OS, Python v10.  The XBC-Recommendation-Engine component was hosted in Azure Container Instances.  The following better represents how things are working together.  

![screenshot](/XBC-Recommendation-Engine/screenshots/XBC-Movie-Rec.drawio.png)  

## Working Application  

Imagine this is a homepage, something similar to Netflix. To use the feature, click the link in the navbar.  
![screenshot](/XBC-Recommendation-Engine/screenshots/homepage.png)  

You'll be presented with all the different genres that exist in the XBC catalog. Choose up to 3 of your favorite genres.  
![screenshot](/XBC-Recommendation-Engine/screenshots/genre_selection.png)  

The application will give you 15 randomly chosen options from a filtered dataset for each genre you selected. Choose up to 10 movies that you have seen and liked.  
![screenshot](/XBC-Recommendation-Engine/screenshots/movie_selection.png)  
![screenshot](/XBC-Recommendation-Engine/screenshots/movie_selection2.png)  
![screenshot](/XBC-Recommendation-Engine/screenshots/movie_selection3.png)  

If you don't like the options you're given, reshuffle the options to get new movies then select up to 10 movies.  
![screenshot](/XBC-Recommendation-Engine/screenshots/shuffle.png)  

Let the recommendation engine suggest 10 movies that you may like.  
![screenshot](/XBC-Recommendation-Engine/screenshots/movie_recommendations.png)  

Click 'More Info' to read a movie description and get more information.  
![screenshot](/XBC-Recommendation-Engine/screenshots/more_info.png)

To maintain tranpsarency with the customer, XBC wants to reassure their users of how these decisions were made. The engine uses content-based filtering with cosine similarity, taking the movies the user picked and comparing them against other movies in the film library on certain features.  The highest cosine similarity scores are recommended.  
![screenshot](/XBC-Recommendation-Engine/screenshots/insights.png)  
![screenshot](/XBC-Recommendation-Engine/screenshots/insights2.png)  