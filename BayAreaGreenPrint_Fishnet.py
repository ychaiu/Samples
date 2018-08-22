# Bay Area Greenprint
# Updated 2018-06-14 by YCZ

# To automate process of incorporating new layers into the fishnet
# Process order: Input vector layer, dissolve, intersect with fishnet, extract points, spatial join to main fishnet
# Assumes that input layers have been custom filtered, processed, and standardized
# Assumes projection to NAD 83 Teale Alberes (meters)

# Import packages to access modules
import arcpy
import os
import string

# Set up toolbox
class Toolbox(object):
    def __init__(self):
        # Define the toolbox (the name of the toolbox is the name of the .pyt file).
        self.label = "Fishnet Toolbox"
        self.alias = "Fishnet Toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [FishnetProcessing]

# Set up parameters and functions	
class FishnetProcessing(object):
    def __init__(self):
        # Define the tool (tool name is the name of the class).
        self.label = "FishnetProcessing"
        self.description = "This tool processes input layers and adds them to the Bay Area Greenprint Fishnet"
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Define parameter definitions

        # First parameter - Select the layer to add to the fishnet
        param0 = arcpy.Parameter(
            displayName="Input Feature Layer",
            name="inputFeature",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        # Second parameter - Designate output folder where fishnet interim layers will be stored 
        param1 = arcpy.Parameter(
            displayName="Interim File Path",
            name="interimPath",
            datatype="DEFeatureDataset",
            parameterType="Required",
            direction="Input")

        # Third parameter - Fishnet template used in the intersect
        param2 = arcpy.Parameter(
            displayName="Fishnet Template",
            name="fishnetPath",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        # Fourth parameter - Fishnet to be appended to
        param3 = arcpy.Parameter(
            displayName="Main Fishnet",
            name="fishnetMain",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        # Fifth parameter - Name of calculate field
        param4 = arcpy.Parameter(
            displayName="Field name for Acreage, Length, or Point Count Field",
            name="fieldName",
            datatype="GPType",
            parameterType="Required",
            direction="Input")

        # Sixth parameter
        param5 = arcpy.Parameter(
            displayName="Name to be Appended to Fishnet",
            name="fishnetName",
            datatype="GPType",
            parameterType="Required",
            direction="Input")

        params = [param0, param1, param2, param3, param4, param5]

        return params

    def isLicensed(self):
        # Set whether tool is licensed to execute.
        return True

    def initializeParameters(self):
        # Refine the properties of a tool's parameters. 
        # This method is called when the tool is opened.
        return

    def updateParameters(self, params):
        # Modify the values and properties of parameters before internal
        # validation is performed.  This method is called whenever a parameter
        # has been changed.
        return

    def updateMessages(self,params):
        # Modify the messages created by internal validation for each tool parameter.
        # This method is called after internal validation.
        
        # If field name entered for parameter 4 exceeds 10 characters, produce error message
        if params[4].altered:
            if len(str(params[4].value)) > 10:
                params[4].setErrorMessage(
                    "Field name cannot exceed ten characters.")

        # If name for parameter 5 contains any special characters, produce error message
        if params[5].altered:
            invalidChars = set(string.punctuation)
            if any (char in invalidChars for char in str(params[5].value)):
                params[5].setErrorMessage(
                    "String cannot include any special characters or underscores.")
        return

    def execute(self, parameters, messages):
        # The source code of the tool

        # Allow files to be overwritten
        arcpy.env.overwriteOutput = True

		# Set variables equal to input parameters
        inputFeature = parameters[0].valueAsText
        interimPath = parameters[1].valueAsText
        fishnetPath = parameters[2].valueAsText
        fishnetMain = parameters[3].valueAsText
        fieldName = parameters[4].valueAsText
        fishnetName = parameters[5].valueAsText

        # Set workspace equal to inputFeature to access Describe Object and its properties
        arcpy.env.workspace = inputFeature

        # Identify data type of the input feature
        desc = arcpy.Describe(inputFeature)
        shapeType = desc.shapeType

        # Identify name of the input feature
        fileName = desc.baseName

        # If feature is a line, polyline, or polygon, then process as follows
        if shapeType == "Line" or shapeType == "Polyline" or shapeType == "Polygon":
            
            # Dissolve feature
            fcDissolve = os.path.join (interimPath, fileName) + "_dissolve"
            arcpy.AddMessage ("Dissolving "+ fileName)
            arcpy.Dissolve_management(inputFeature, fcDissolve)
            arcpy.AddMessage ("Dissolving of "+ fileName + " complete")

            # Intersect with fishnet template
            fishnetInputs = [fcDissolve, fishnetPath]
            desc = arcpy.Describe (fcDissolve)
            fishnetIntersect = os.path.join (interimPath,"fishnet_intersect_") + desc.baseName 
            arcpy.AddMessage ("Intersecting " + fileName + " with fishnet")
            arcpy.Intersect_analysis (fishnetInputs, fishnetIntersect)
            arcpy.AddMessage ("Intersecting of " + fileName + " with fishnet complete")

            # Create new field, calculate acreage or length

            # If feature is a polygon, calculate acreage
            if shapeType == "Polygon":

                # Add field for acres
                arcpy.AddField_management (fishnetIntersect, fieldName, "DOUBLE")
                fields = ["SHAPE@AREA", fieldName]
                arcpy.AddMessage ("Calculating acreage for " + fileName)

                # Iterate through each cell, calculate acreage for intersected cells
                with arcpy.da.UpdateCursor (fishnetIntersect, fields) as cursor:
                    for row in cursor:
                        row [1] = row[0]*0.000247
                        cursor.updateRow(row)
                    # Delete row and cursor to clear in-memory space
                    del row, cursor
                arcpy.AddMessage ("Calculating acreage for " + fileName + " complete")

            # If feature is a line, calculate length in miles
            elif shapeType == "Line" or shapeType == "Polyline":

                # Add field for length
                arcpy.AddField_management (fishnetIntersect, fieldName, "DOUBLE")
                fields = ["SHAPE@LENGTH", fieldName]
                arcpy.AddMessage ("Calculating length for " + fileName)
                with arcpy.da.UpdateCursor (fishnetIntersect, fields) as cursor:
                    for row in cursor:
                        row [1] = row[0]/1609.344
                        cursor.updateRow(row)
                    # Delete row and cursor to clear in-memory space
                    del row, cursor
                arcpy.AddMessage ("Calculating length for " + fileName + "complete")


            # Convert feature class to pts
            fishnetPoint = fishnetIntersect + "_pt"
            arcpy.AddMessage ("Converting " + fileName + " to points")
            arcpy.FeatureToPoint_management (fishnetIntersect, fishnetPoint) 
            arcpy.AddMessage ("Converting " + fileName + " to points complete")

            # Prepare fieldmapping and field maps for a spatial join of the calculated field to the fishnet

            # Define inputs
            targetFeature = fishnetMain
            joinFeature = fishnetPoint
            finalFeature = fishnetMain + "_" + fishnetName

            # Create fieldmaps for the join field and the target fields
            joinFM = arcpy.FieldMap()
            fishnetFMS = arcpy.FieldMappings()
            fishnetFMS.addTable(targetFeature)
            
            # Add the join field (calculated acres or length) to the field map, and define properties
            joinFM.addInputField (joinFeature, fieldName)
            joinName = joinFM.outputField
            joinName.name = fieldName
            joinName.aliasName = fieldName

            # Add the join field map to the overall field mapping
            fishnetFMS.addFieldMap(joinFM)

            # Spatial join the input feature layer to the main fishnet
            arcpy.AddMessage ("Spatial joining " + fileName + " to the fishnet")
            arcpy.SpatialJoin_analysis (targetFeature, joinFeature, finalFeature, "#", "#", fishnetFMS, "INTERSECT")
            arcpy.AddMessage ("Spatial joining " + fileName + " to the fishnet complete")

            # Delete the "JOIN_COUNT" field created
            deleteFields = ["JOIN_COUNT", "Join_Count", "TARGET_FID"]
            arcpy.DeleteField_management (finalFeature, deleteFields)

        # If the input feature is point type
        elif shapeType == "Point" or shapeType == "Multipoint":

            # Explode input to ensure proper point density calculation
            arcpy.AddMessage ("Exploding" + fileName)
            explodeFile = interimPath + "/" + fileName + "_explode"
            arcpy.MultipartToSinglepart_management (inputFeature, explodeFile)
            arcpy.AddMessage ("Exploding " + fileName  + "completed")

            # Prepare fieldmapping and field maps for a spatial join to the fishnet

            # Define inputs
            targetFeature = fishnetMain
            joinFeature = explodeFile
            tempFeature = fishnetMain + "_" + fishnetName + "_temp"

            # Create field mapping, add fishnet fields to the field map
            fishnetFMS = arcpy.FieldMappings()
            fishnetFMS.addTable(targetFeature)

            # Spatial join the input feature layer to the main fishnet
            arcpy.AddMessage ("Spatial Joining " + fileName + " to the Fishnet")
            arcpy.SpatialJoin_analysis (targetFeature, joinFeature, tempFeature, "#", "#", fishnetFMS, "INTERSECT")
            arcpy.AddMessage ("Spatial Joining " + fileName + " to the Fishnet complete")

            # Delete extra fields
            arcpy.DeleteField_management (tempFeature, "TARGET_FID")

            # ArcMap will create a "JOIN_COUNT" field in the process of a spatial join
            # "JOIN_COUNT" is the same as point density
			# Using the Feature Class Conversion tool, rename "JOIN_COUNT" field to user-designated name

            # Define inputs
            inFeature = tempFeature
            finalFeature = fishnetMain + "_" + fishnetName

            # Create field mapping and add respective field maps
            finalFMS = arcpy.FieldMappings()
            finalFMS.addTable(inFeature)
            tempFM = arcpy.FieldMap()

            # Add "JOIN_COUNT" to the field map, and rename
            tempFM.addInputField (inFeature, "Join_Count")
            tempName = tempFM.outputField
            tempName.name = fieldName
            tempName.aliasName = fieldName
            tempFM.outputField = tempName

            # Add to the field mapping
            finalFMS.addFieldMap(tempFM)

            # Name of final fishnet
            desc = arcpy.Describe (fishnetMain)
            partOne = desc.baseName
            partTwo = fishnetName
            finalName = partOne + "_" + partTwo

            # Rename field, save as new feature class
            arcpy.AddMessage ("Renaming [Join_Count] to designated name")
            arcpy.FeatureClassToFeatureClass_conversion(inFeature, desc.path, finalName, "#", finalFMS)
            arcpy.AddMessage ("Renaming [Join_Count] to designated name complete")

            # Clean up files and fields
            arcpy.Delete_management (tempFeature)
            arcpy.DeleteField_management (finalFeature, "Join_Count")

        return