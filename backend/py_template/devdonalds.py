from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re

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
	# TODO: implement me
	return 'not implemented', 500


# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
