# Your First Script With Kryptonite

By this point, you've hopefully installed Kryptonite and are ready to start writing some code! This tutorial will guide you through the basics of using Kryptonite to interact with TVNZ's API.

First, however, it's a good idea if we take a quick look at how Kryptonite is structured. If you look in the main Kryptonite folder, you'll one specific folder name `kryptonite`. This folder contains all the code that makes up the Kryptonite library.

Inside this folder, you'll find a number of Python files, most importantly the `kryptonite.py` file. This is the file that contains the different classes for each streaming service. For example, the `Tvnz` class is used to interact with TVNZ's API.

With that out of the way, let's get onto some code!

## Your First Script

For our first project using kryptonite, we'll create a simple script to search for a show on TVNZ and then get a list of all the episodes for that show.

To get started, we'll create a new file in the main Kryptonite folder. You can name this file whatever you like, but for this tutorial, we'll call it `main.py`.

As you'd expect, the first thing we need to do is import the `kryptonite` module. This is done with the following line:

```python
import kryptonite
```

Now that we have access to kryptonite, we need to create an instance of the `Tvnz` class. This is done with the following line:

```python
api = kryptonite.Tvnz()
```

From now on, we'll be interacting with the `api` object to interact with TVNZ's API. As I mentioned before, the first thing we'll do is search for a show. This is done with the `search` method. The `search` method takes a single argument, the name of the show you want to search for. For example, to search for the show "Shortland Street", you would use the following line:

```python
searchResults = api.search("Shortland Street")
```

This will return a list of search results. Each search result is a dictionary containing information about the show. For example, the `show_id` key contains the ID of the show. If the metadata for a show returned by the search method isn't enough for you, you can use the `get_show` method. This method takes a single argument, the ID of the show you want to get the metadata for. For example, to get the metadata for the first search result, you would use the following line:

```python
metadata = api.get_show(searchResults[0]["show_id"])
```

This will return a dictionary containing information about the show. Just to make sure that we've done everything correctly so far, let's print out the metadata for the show:

```python
print(metadata)
```

With a little luck, you should see a bunch of information about the show printed to the console. If you do, congratulations! You've successfully searched for a show and retrieved its metadata.

Just to recap, here's the full script so far:

```python
import kryptonite

api = kryptonite.Tvnz()

searchResults = api.search("Shortland Street")
metadata = api.get_show(searchResults[0]["show_id"])
print(metadata)
```

## Going a Step Further

Now that we've successfully searched for a show and retrieved its metadata, let's take things a step further. In this section, we'll get a list of all the episodes for the show that we searched for. 

To do this, we'll use the `get_episodes` method. This method takes a single argument, the ID of the show you want to get the episodes for. For example, to get a list of all the episodes for "Shortland Street", which has a show ID of "17009", you would use the following line:

```python
episodeList = api.get_episodes("17009")
```

This will return a very long list of episodes, organized by season. Each episode is a dictionary containing information about the episode. Just to make sure that we've done everything correctly so far, let's print out the list of episodes:

```python
print(episodeList)
```
Interestingly, the get_episodes method can also be used to get a list of episodes for a movie. In this case, you would use the show ID of the movie exactly the same as you would for a show. This is important when downloading videos, as you'll need the video ID to download the video, and the `get_episodes` method is the easiest way to get this information.

Just to recap, here's the full script that we've written:

```python
import kryptonite

api = kryptonite.Tvnz()

searchResults = api.search("Shortland Street")
metadata = api.get_show(searchResults[0]["show_id"])
print(metadata)

episodeList = api.get_episodes(searchResults[0]["show_id"])
print(episodeList)
```

## Conclusion

And that's it! You've successfully written your first script using Kryptonite. In this tutorial, we've covered how to search for a show on TVNZ, get the metadata for that show, and get a list of all the episodes for that show. However, that is just the tip of the iceberg. Kryptonite has a lot more functionality that you can explore, such as downloading videos and subtitles, logging in, and getting user information, all of which we can explore in the other tutorials.