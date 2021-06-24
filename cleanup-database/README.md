# CleanUp Databases
The django webservices in Jupyter-JSC may produce data in their database, without cleaning them properly.  

This should not happen, but it can happen due to unexpected failures, connection losses to the database, network issues, storage issues, bugs in the code.  

We're working on it, to improve these webservices, so that no incorrect data will be left in the database.  

**Until then, we'll use these two scripts to find (findonly.sh) or delete (cleanup.sh) these data.**

You may have to update a few variables
