# nypd-misconduct-dashboard

This project was built as a part of [Hack for the People](https://hackforthepeople.com/) hackathon. You can see a demo of the dashboard [here](https://nypab.xyz). Also, [see the submission on Devpost](https://devpost.com/software/new-york-police-action-board).

## Inspiration

Law enforcement institutions are entrusted with a diverse set of tasks requiring a high degree of integrity within police agencies and their oversight. Where this does not function well, law enforcement officers may become vulnerable to oversight and misconduct. In many non-conflict/conflict situations, it becomes necessary to act upon the complaints by the civilians, often in the form of retraining for police officers with a particular focus on human rights principles. In addition, a longer-term effort is required to establish a framework for police oversight and accountability in order to strengthen integrity within systems of policing.

Hence, we wanted to create a system to create transparency between the Authorities and the civilians to ensure and improve trust within the system. This website provides various insights into the performance of the various law enforcement authorities and displays the patterns/actions taken by the authorities and also helps civilians using Machine Learning methodologies to get estimates about their complaint/request status. We are aware of the effects of bias and other natural parameters when using Machine Learning methods in Sociocultural space, and instead, we commit ourselves to be honest about flaws, transparent in our publishing process, and welcoming of critiques.

## What it Does

NYPAB (New York Police Action Board) provides users a simple and efficient platform for accessing police misconduct allegations against NYPD officers. Along with greater accessibility to this data, it also provides insights into the police accountability system by visualizing various interactive graphs which makes it easier for the general public to better understand the data leading to a better understanding of the system in general.

NYPAB also provides a search tool that helps users find police officers that have had misconduct allegations in the past. The user can see the raw data and also a separate dashboard for individual police officers with information about their previous allegations and outcomes of those cases.

NYPAB also has an experimental tool, where based on the user inputs, a user can get an estimate of the total time the department might take to act upon the user’s complaint based on the historical data.

## How We Built It

We, the team of size 2, started brainstorming on ideas/solutions which can help solve problems within the socio-cultural domain, and we found the lack of transparency and accessibility of police accountability data. We found this dataset that listed information about civil misconduct allegations against NYPD police officers. It was released by New York Civil Liberties Union, less than 24 hours before the hackathon and it showcased a huge socio-cultural problem of police accountability.

We used various tools in the Visualisations and Data Science domain to create this website. We used the Google Cloud VMs, App Engine, and storage services to store the dataset and host the website allowing others to access it. We used Flask for creating a scalable and efficient BackEnd System, and visualization libraries like Plotly to create useful and intuitive graphs. We also used GitHub for efficient project management and an effective communication system to achieve this task.

## Challenges We Ran Into

One of the main challenges was to extract meaningful patterns from the dataset using various data transformation operations. We got to learn various new tools and techniques to handle such large data efficiently during this process. Also, integrating these visualizations and the Machine Learning model with various Software Development tools such as HTML, etc was also challenging and a fun experiment to learn.

## Future Scope of NYPAB

We have learned that there is many more solutions space left to explore to tackle this issue with available data, and the insights and there is much more space remaining to help users access such data with more transparency and authenticity. We also know that using Machine Learning solutions in the social/cultural domain is still the field that needs a lot of research to achieve the level of accuracy and fairness. The societal issues may take many forms, but they all entail the design of models from a human-centered perspective, incorporating human-relevant requirements and constraints, and the solutions will require attributes such as fairness, privacy, and anonymity, explainability, and interpretability, but also some broader societal issues, such as ethics and legislation.

We hope to incorporate a feature that allows users to access to complaint forms based on requests and also perform topic modeling of these documents to identify key issues faced by civilians in their complaints, respecting data privacy terms and anonymity.