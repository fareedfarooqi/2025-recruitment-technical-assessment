from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re
import json
from dataclasses import asdict

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	type: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	type: str
	name: str
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	type: str
	name: str
	cook_time: int

@dataclass
class CoobookError(Exception):
	pass

# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook = []

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str | None]:
	"""
	This function is used to clean up poorly formatted food names by removing unwanted characters and bad formatting.

	The function will:
		- Replace whitespaces, udnerscores or hypens (if they appear one or more times) with a single whitespace.
		- Remove any and all characters that are not letters ('A-Z' or 'a-z') or a single space character with no spaces.
		- Capitalise the first letter of every word in the recipe name.
		- Return the updated food name given that it's length is greater than 0. Otherwise it will return 'None'.
	"""
	recipe_name = re.sub(r'[\s_-]+', " ", recipeName)
	recipe_name = re.sub(r'[^A-Za-z ]+', "", recipe_name)
	recipe_name = recipe_name.title()

	return recipe_name if len(recipe_name) > 0 else None

# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	"""
	This function is used to create an entry for a recipe or ingredient into our cookbook.

	This function will:
		- Retrieve the data in JSON format.
		- Does appropriate error checks such as to verify if the JSON data object passed in has a type and if it is either 'recipe' or 'ingredient'. We also check to see if the 'cookTime' is greater or equal to 0 for an ingredient. We also check for any duplicate entries into our cookbook and 'requiredItems' (for Recipes only).
		- Convert the respective data to an instance of either a 'Recipe' or 'Ingredient' (depending on what was passed in as our JSON data) and then append it to our cookbook.

	"""
	# I need to get the JSON body that is sent over HTTP to us.	
	data = request.get_json()
	
	# So I need to validate that the JSON we receive has the 'type' key and the appropriate values.
	if 'type' not in data:
		return jsonify({"error": "The type is missing! Please add the type to your request!!!"}), 400
	elif data['type'] not in ['recipe', 'ingredient']:
		return jsonify({"error": "Please use the specified type of either 'recipe' or 'ingredient'."}), 400
	
	# This was an extra check (not part of spec). I am doing it in case.
	if data['type'] == "recipe" and "requiredItems" not in data:
		return jsonify({"error": "Please ensure your recipe has a requiredItems field."}), 400

	# We need to check if the data passed in is of type 'ingredient', if it is we check if the 'cookTime' is less than 0 (if so return an error).
	if data['type'] == "ingredient" and data['cookTime'] < 0:
		return jsonify({"error": "Please enter a valid 'cookTime' that is greater or equal to 0!!!"}), 400
	
	# We also need to check if the entry we are making in the cookbook is unique.
	for entry in cookbook:
		if entry.name == data["name"]:
			return jsonify({"error": "An entry of this name already exists. Please provide unique entry names!!!"}), 400

	# Before adding the item to our cookbook, we need to see if there are any duplicates in 'requiredItems'.
	required_items_list = []
	if data['type'] == "recipe":
		for required_item in data["requiredItems"]:
			required_items_list.append(RequiredItem(name=required_item["name"], quantity=int(required_item["quantity"]))) # We also convert quantity to an integer (in case).
	
	if validate_required_items(required_items_list):
		return jsonify({"error": "There are duplicate entires in 'requiredItems'. It can only contain unique elements!!!"}), 400

	# All cases above pass so we can add the entry into our cookbook depending upon if it is a recipe or an ingredient.
	if data['type'] == "recipe":
		cookbook.append(Recipe(
			type=data["type"],
			name=data["name"],
			required_items=required_items_list
		))
	
	if data['type'] == "ingredient":
		cookbook.append(Ingredient(
			type=data["type"],
			name=data["name"],
			cook_time=int(data["cookTime"]) # Converting 'cookTime' to an integer in case it's passed as a string.
		))
	
	pretty_output = json.dumps([asdict(entry) for entry in cookbook], indent=2)
	print(pretty_output)
	print(cookbook)

	return 'success', 200

def validate_required_items(required_items_list):
	"""
	This is a helper function that checks to see if an item with the same name is part of the 'requiredItems' field from our JSON data. If an item is a duplicate we simply return 'True', otherwise we return 'False'.
	"""
	seen = set()

	for item in required_items_list:
		item_name = item.name
		if item_name in seen:
			return True
		seen.add(item_name)
		
	return False

# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():

	# We need to get the name of the recipe from the URL.
	print(cookbook)
	query_name = request.args.get("name")

	# We need to check if the recipe exists in our cookbook (and if the 'query_name' passed in is a recipe or ingredient).
	recipte_entry = None
	for item in cookbook:
		if item.name == query_name and item.type == 'recipe':
			recipe_exists = True
			recipte_entry = item
		elif item.name == query_name and item.type == 'ingredient':
			return jsonify({"error": "An ingredient was passed in. Please ONLY pass in a valid recipe!!!"}), 400
	
	# If the recipe does not exist in our cookbook we return an error.
	if recipte_entry is None:
		return jsonify({"error": "Recipe is not in the cookbook!!!"}), 400
	
	# We must get the base ingredients of our recipe. Our 'get_base_ingredients' can raise an error
	# if a recipe or an ingredient is not in our cookbook.
	try:
		list_of_base_ingredients = get_base_ingredients(recipte_entry)
	except Exception as e:
		return jsonify({"error": str(e)}), 400
	
	total_cook_time = get_total_cook_time(list_of_base_ingredients)

	recipe_summary = {
		"name": query_name,
		"cookTime": total_cook_time,
		"ingredients": list_of_base_ingredients
	}

	return recipe_summary, 200

def get_base_ingredients(recipe, multiplier=1):
	base_ingredients = {}

	for required_item in recipe.required_items:
		entry = None
		for item in cookbook:
			if item.name == required_item.name:
				entry = item
				break
		
		# We check to see if the entry (our recipe or the ingredient) was even in the cookbook. If not we return an error.
		if entry is None:
			raise CoobookError("The recipe contains recipes or ingredients that aren't in the cookbook.")
		
		total_quantity = required_item.quantity * multiplier

		# Now we need to see if what we are currently processing in the loop is an 'ingredient' or a 'recipe'.
		if entry.type == "ingredient":
			# This means we are at a base ingredient we can simply add it to our dict.
			if required_item.name in base_ingredients:
				base_ingredients[required_item.name] += total_quantity
			else:
				# We create a new entry into our dict for this base ingredient.
				base_ingredients[required_item.name] = total_quantity
		elif entry.type == "recipe":
			# We must then recursively expand in order to get our base ingredients from this recipe.
			# Because recipe could have a recipe which could have a recipe etc.
			sub_ingredients = get_base_ingredients(entry, multiplier=total_quantity)

			# We must now add the base 'sub_ingredients' to our dict.
			for ingredient_name, ingredient_quantity in sub_ingredients.items():
				if ingredient_name in base_ingredients:
					base_ingredients[ingredient_name] += ingredient_quantity
				else:
					base_ingredients[ingredient_name] = ingredient_quantity
	
	return base_ingredients

def get_total_cook_time(list_of_base_ingredients):
	print(list_of_base_ingredients)
	total_cook_time = 0

	# We loop through our base ingredients list and our cook book in order to get the time it takes
	# to cook the base ingredient.
	for ingredient, quantity in list_of_base_ingredients.items():
		for item in cookbook:
			if item.name == ingredient:
				total_cook_time += item.cook_time * quantity
	
	return total_cook_time

# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
