# How to set up
## Run through terminal
```
1. Clone the repository
2. copy .env.example to .env
3. fill in the .env file
4. run 'python main.py'
```
## Run through docker
```
1. Clone the repository
2. run 'docker build -t <repository>:<tag> .' (don't forget the dot)
3. run 'docker run -e DISCORD_TOKEN=<token> -e X_RAPIDAPI_KEY=<rapidapi-key> <respository>:<tag>'
or
3. copy .env.example to .env
4. fill in the .env file
5. run 'docker run --env-file .env <repository>:<tag>'
```