would like to have python script command based application to get usage info (in and out tokens ) , cost , current balance 
would like to have local db single file like scite3 to store llm usage info with date and time stamp whenever I refresh from python app ; also should have proivder info example openai ,gemini , claude , openrouter ,deepseek , etc with admin connection inforation like url or command , uid or api key
would like to have log mechanisum in case of further troubleshooting 
paython app should have
    1. to fetch llm usage info (update db with info) individual
    2. fetch on the basis of configured provider (selection from configured llms info)
    3. admin to adde llm addition with provider and provider info as required to connect to provider
    4. list all configured provider detail information and crud operation
    5. logs enable y/n ; once enable need to create <usageapp-timestamp>.log creation storing all activity ; in case logs enabled then any options from 1 to 4 above need to have single log file as mentioned