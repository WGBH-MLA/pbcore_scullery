
# %%
# Import modules from Python standard library
import argparse
import os
import glob
import xml.etree.ElementTree as ET
import csv
from pprint import pprint

# import installed modules
import pandas as pd

# Set the display options to show all rows and columns
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

pd.set_option('display.width',2000)


############################################################################
# %%
# Define tablify function
def tablify( pbcore_dir:str ):
    """
    Build tables of assets and instantiations (as Python lists of lists)
    """

    print("Using directory:", pbcore_dir)

    if not os.path.isdir(pbcore_dir):
        print("Error:  Invalid directory path for PBCore files.")
        raise Exception("Invalid directory path for PBCore files.")

    filenames = os.listdir(pbcore_dir)
    xmlfilenames = glob.glob(pbcore_dir + "/*.xml")

    if len(filenames) > len(xmlfilenames):
        print("Warning: Working directory includes files with extension other than .xml")
        print("         or perhaps a file named simply '.xml'.")

    # define namespace prefix for XML elements
    ns = {"pbcore": "http://www.pbcore.org/PBCore/PBCoreNamespace.html"}

    # The initial catalog tables
    assttbl = []
    insttbl = []

    #### CAT-AUD ##############################################
    # variables for counting or compiling weird things
    multici_guids = []
    noci_guids = []
    mismatch_dig_media_types_guids = {}
    #### CAT-AUD ##############################################

    # For each XML file, 
    #   - add a row to the asset table
    #   - add zero or more rows to the instantiations table
    for fn in filenames:

        # read XML file (making sure we can parse it)
        fpath = pbcore_dir + "/" + fn

        try:
            tree = ET.parse(fpath)
        except ET.ParseError as e:
            print(f"Error in XML parsing for file {fn}: {e}")
        except Exception as e:
            print(f"An error occurred with file {fn}: {e}")

        # Get the root element of the XML tree
        # This should be a `pbcoreDescriptionDocument`.
        root = tree.getroot()

        root_tag = root.tag
        root_tag_no_ns = root_tag.split('}')[-1] if '}' in root_tag else root_tag
        if root_tag_no_ns != "pbcoreDescriptionDocument":
            print("Warning: The root element is:", root_tag_no_ns)
            print("Skipping", fn)
            continue
         

        # get all the values we want
        # (If an element is missing, assign empty string to the variable)

        #
        # Identifier elements 
        #
        # Asset.id
        # The raw text from the PBCore is stored as the `aapb_pbcore_id`
        # The normalized "guid" (without / or _) is stored as `asset_id`
        att = "[@source='http://americanarchiveinventory.org']"
        e = root.find("pbcore:pbcoreIdentifier"+att,ns)
        aapb_pbcore_id = e.text if e is not None else ""
        asset_id = aapb_pbcore_id.replace('/', '-').replace('_', '-')

        # Asset.sonyci_id
        #att = "[@source='Sony Ci']"
        #e = root.find("pbcore:pbcoreIdentifier"+att,ns)
        #sonyci_id = e.text if e is not None else ""

        # Asset.sonyci_id
        # Takes the Sony Ci ID from the first non-empty matching element
        att = "[@source='Sony Ci']"
        es = root.findall("pbcore:pbcoreIdentifier"+att,ns)
        sonyci_id = ""
        for e in es:
            if (not sonyci_id and e.text):
                sonyci_id = e.text

        #
        # Annotation elements 
        #
        # Asset.organization
        att = "[@annotationType='organization']"
        e = root.find("pbcore:pbcoreAnnotation"+att,ns)
        organization = e.text if e is not None else ""

        # Asset.level_of_user_access
        att = "[@annotationType='Level of User Access']"
        e = root.find("pbcore:pbcoreAnnotation"+att,ns)
        level_of_user_access = e.text if e is not None else ""

        # Asset.special_collections
        # handling multiple values
        att = "[@annotationType='special_collections']"
        es = root.findall("pbcore:pbcoreAnnotation"+att,ns)
        tlist = [ e.text for e in es ]
        special_collections = ','.join(tlist)

        # Asset.transcript_status
        att = "[@annotationType='Transcript Status']"
        e = root.find("pbcore:pbcoreAnnotation"+att,ns)
        transcript_status = e.text if e is not None else ""

        # Asset.transcript_url
        att = "[@annotationType='Transcript URL']"
        e = root.find("pbcore:pbcoreAnnotation"+att,ns)
        transcript_url = e.text if e is not None else ""

        # Proxy Start Time
        att = "[@annotationType='Proxy Start Time']"
        e = root.find("pbcore:pbcoreAnnotation"+att,ns)
        proxy_start_time = e.text if e is not None else ""

        #
        # Date elements 
        #
        # Asset.broadcast_date
        att = "[@dateType='Broadcast']"
        e = root.find("pbcore:pbcoreAssetDate"+att,ns)
        broadcast_date = e.text if e is not None else ""

        # Asset.created_date
        att = "[@dateType='Created']"
        e = root.find("pbcore:pbcoreAssetDate"+att,ns)
        created_date = e.text if e is not None else ""

        # Asset.copyright_date
        att = "[@dateType='Copyright']"
        e = root.find("pbcore:pbcoreAssetDate"+att,ns)
        copyright_date = e.text if e is not None else ""

        # Asset.date (no @dateType)
        es = root.findall("pbcore:pbcoreAssetDate",ns)
        esnoat = [e for e in es if 'dateType' not in e.attrib]  
        date = esnoat[0].text if len(esnoat) > 0 else ""

        # Canonical date
        # Use a simple heuristic to set a single canonical date, given that 
        # there might be several dates associated with the asset
        if date:
            single_date = date
        elif copyright_date:
            single_date = copyright_date
        elif created_date:
            single_date = created_date
        elif broadcast_date:
            single_date = broadcast_date
        else:
            single_date = ""


        #
        # Title elements 
        #
        # Asset.series_title
        att = "[@titleType='Series']"
        e = root.find("pbcore:pbcoreTitle"+att,ns)
        series_title = e.text if e is not None else ""

        # Asset.program_title
        att = "[@titleType='Program']"
        e = root.find("pbcore:pbcoreTitle"+att,ns)
        program_title = e.text if e is not None else ""

        # Asset.episode_title
        att = "[@titleType='Episode']"
        e = root.find("pbcore:pbcoreTitle"+att,ns)
        episode_title = e.text if e is not None else ""

        # Asset.episode_number
        att = "[@titleType='Episode Number']"
        e = root.find("pbcore:pbcoreTitle"+att,ns)
        episode_number = e.text if e is not None else ""

        # Asset.segment_title
        att = "[@titleType='Segment']"
        e = root.find("pbcore:pbcoreTitle"+att,ns)
        segment_title = e.text if e is not None else ""

        # Asset.raw_footage_title
        att = "[@titleType='Raw Footage']"
        e = root.find("pbcore:pbcoreTitle"+att,ns)
        raw_footage_title = e.text if e is not None else ""

        # Asset.promo_title
        att = "[@titleType='Promo']"
        e = root.find("pbcore:pbcoreTitle"+att,ns)
        promo_title = e.text if e is not None else ""

        # Asset.clip_title
        att = "[@titleType='Clip']"
        e = root.find("pbcore:pbcoreTitle"+att,ns)
        clip_title = e.text if e is not None else ""

        # Asset.title (no @titleType)
        es = root.findall("pbcore:pbcoreTitle",ns)
        esnoat = [e for e in es if 'titleType' not in e.attrib]
        title = esnoat[0].text if len(esnoat) > 0 else ""

        # Canonical title
        # Build a single canonical title, given that there might be several
        # titles associated with the asset
        consolidated_title = ""
        if series_title:
            consolidated_title += (series_title + ": ")
        if episode_number:
            consolidated_title += ("No. " + episode_number + ": ")
        consolidated_title += episode_title
        consolidated_title += program_title
        consolidated_title += segment_title
        consolidated_title += raw_footage_title
        consolidated_title += promo_title
        consolidated_title += clip_title
        if title:
            if consolidated_title:
                consolidated_title += (" " + title)
            else:
                consolidated_title += title


        #
        # Other elements 
        #
        # Asset.asset_types
        att = ""
        e = root.find("pbcore:pbcoreAssetType"+att,ns)
        asset_type = e.text if e is not None else ""


        #
        # Creator and contributor elements
        #

        # Asset.producing_organization
        pbcreators = root.findall("pbcore:pbcoreCreator",ns)
        crole_e = None    
        creator_e = None
        producing_organization = ""
        for pbcreator_e in pbcreators:
            crole_e = pbcreator_e.find("pbcore:creatorRole",ns)
            crole = crole_e.text if crole_e is not None else ""
            creator_e = pbcreator_e.find("pbcore:creator",ns)
            creator = creator_e.text if creator_e is not None else ""
            #print("Creator role:", crole, "Creator:", creator)
            if crole == "Producing Organization":
                producing_organization = creator


        """
        # DigitalInstantiation.media_type for the asset
        # (Note: This is not an element that is part of the asset records, but
        #  we need to associate a media type with the asset; so we make an 
        #  intelligent choice among the media types in the instantiation records.)
        # First, narrow down to the digital instantiations
        # Then, if there are serveral, prioritize video, then audio
        insts = root.findall(".//pbcore:pbcoreInstantiation",ns)
        dig_mts = []  # create list of media types for digial instantiations
        for inst in insts:
            if inst.find("pbcore:instantiationDigital",ns) is not None:
                mte = inst.find("pbcore:instantiationMediaType",ns)
                if mte is not None:
                    dig_mts.append(mte.text)
        if len(dig_mts) == 0:
            media_type = ''
        elif 'Moving Image' in dig_mts:
            media_type = 'Moving Image'
        elif 'Sound' in dig_mts:
            media_type = 'Sound'
        else:
            media_type = dig_mts[0]
        """

        # DigitalInstantiation.media_type for the asset
        # (Note: This is not an element that is part of the asset records, but
        #  we need to associate a media type with the asset; so we make an 
        #  intelligent choice among the media types in the instantiation records.)
        insts = root.findall(".//pbcore:pbcoreInstantiation",ns)
        dig_mts = []  # create list of media types for digial instantiations
        phs_mts = []  # create list of media types for physical instantiations
        for inst in insts:
            mte = inst.find("pbcore:instantiationMediaType",ns)
            if mte is not None:
                if inst.find("pbcore:instantiationDigital",ns) is not None:
                    dig_mts.append(mte.text)
                elif inst.find("pbcore:instantiationPhysical",ns) is not None:
                    phs_mts.append(mte.text)
        if 'Moving Image' in dig_mts:
            media_type = 'Moving Image'
        elif 'Sound' in dig_mts:
            media_type = 'Sound'
        elif 'Moving Image' in phs_mts:
            media_type = 'Moving Image'
        elif 'Sound' in phs_mts:
            media_type = 'Sound'
        elif len(dig_mts) > 0:
            media_type = dig_mts[0]
        elif len(phs_mts) > 0:
            media_type = phs_mts[0]
        else:
            media_type = ''

        # Proxy duration 
        # (Note: This is not an element that is part of the asset records, but it
        #  is useful to infer this where possible.)
        # Take the duration of the first digital instatniation where the generation 
        # equals "Proxy"
        proxy_duration = ""
        insts = root.findall(".//pbcore:pbcoreInstantiation",ns)
        for inst in insts:
            if inst.find("pbcore:instantiationDigital",ns) is not None:
                e = inst.find("pbcore:instantiationGenerations",ns)
                if (not proxy_duration) and e is not None:
                    if e.text == "Proxy":
                        e = inst.find("pbcore:instantiationDuration",ns)
                        if e is not None:
                            proxy_duration = e.text


        # Instantiation records
        insts = root.findall(".//pbcore:pbcoreInstantiation",ns)
        for inst in insts:

            # Instantiation identifers
            # handling multiple values by concatenating all of them into a |-separated list
            att = ""
            es = inst.findall("pbcore:instantiationIdentifier",ns)
            # e.text is cast as str to handle a case where the element exists but
            # has no text as with this guid: cpb-aacip-111-02c8693q        
            tlist = [ str(e.text) for e in es ]
            inst_identifiers = '|'.join(tlist)

            # Instantiation media type
            att = ""
            e = inst.find("pbcore:instantiationMediaType"+att,ns)
            inst_media_type = e.text if e is not None else ""

            # Instantiation date
            att = ""
            e = inst.find("pbcore:instantiationDate"+att,ns)
            inst_date = e.text if e is not None else ""

            # Instantiation digital format
            att = ""
            e = inst.find("pbcore:instantiationDigital"+att,ns)
            inst_digital_format = e.text if e is not None else ""

            # Instantiation physical format
            att = ""
            e = inst.find("pbcore:instantiationPhysical"+att,ns)
            inst_physical_format = e.text if e is not None else ""

            # Instantiation generations
            att = ""
            e = inst.find("pbcore:instantiationGenerations"+att,ns)
            inst_generations = e.text if e is not None else ""

            # Instantiation duration
            att = ""
            e = inst.find("pbcore:instantiationDuration"+att,ns)
            inst_duration = e.text if e is not None else ""

            # Instantiation location
            att = ""
            e = inst.find("pbcore:instantiationLocation"+att,ns)
            inst_location = e.text if e is not None else ""

            # Add the collected instantiation-level values to the table
            insttbl.append([asset_id,
                            inst_identifiers,
                            inst_media_type,
                            inst_digital_format,
                            inst_physical_format,
                            inst_generations,
                            inst_duration,
                            inst_location
                            ])


        # Add the collected asset-level values to the table
        assttbl.append([asset_id,
                        aapb_pbcore_id, 
                        sonyci_id,
                        media_type,
                        asset_type, 
                        organization,
                        level_of_user_access,
                        special_collections,
                        transcript_status,
                        transcript_url,
                        proxy_start_time,
                        broadcast_date,
                        created_date,
                        copyright_date,
                        date,
                        single_date,
                        series_title,
                        program_title,
                        episode_title,
                        episode_number,
                        segment_title,
                        raw_footage_title,
                        promo_title,
                        clip_title,
                        title,
                        consolidated_title,
                        producing_organization,
                        proxy_duration
                        ])


        #### CAT-AUD ##############################################
        # Find all those with multiple SonyCi IDs
        att = "[@source='Sony Ci']"
        es = root.findall(".//pbcore:pbcoreIdentifier"+att,ns)
        if len(es) == 1:
            single_sonyci_id = True
        elif len(es) < 1:
            single_sonyci_id = False
            noci_guids.append(asset_id)
        else:
            single_sonyci_id = False
            multici_guids.append(asset_id)


        # testing for mixed types of digital instantiations
        if ( len(dig_mts) > 1 and 
            not all(mt==dig_mts[0] for mt in dig_mts) and
            'Moving Image' in dig_mts and
            'Sound' in dig_mts ):
            mismatch_dig_media_types_guids[asset_id] = dig_mts

        #### CAT-AUD ##############################################

    return ( assttbl, insttbl )

############################################################################
# %%
# Define infrmae function
def inframe( assttbl, insttbl ):
    """
    Create dataframes from tables
    """

    asstcols = ["asset_id",
                "aapb_pbcore_id", 
                "sonyci_id",
                "media_type",
                "asset_type", 
                "organization",
                "level_of_user_access",
                "special_collections",
                "transcript_status",
                "transcript_url",
                "proxy_start_time",
                "broadcast_date",
                "created_date",
                "copyright_date",
                "date",
                "single_date",
                "series_title",
                "program_title",
                "episode_title",
                "episode_number",
                "segment_title",
                "raw_footage_title",
                "promo_title",
                "clip_title",
                "title",
                "consolidated_title",
                "producing_organization",
                "proxy_duration"]

    instcols = ["asset_id",
                "inst_identifiers",
                "inst_media_type",
                "inst_digital_format",
                "inst_physical_format",
                "inst_generations",
                "inst_duration",
                "inst_location"]

    asstdf = pd.DataFrame(assttbl, columns=asstcols)

    instdf = pd.DataFrame(insttbl, columns=instcols)

    joindf = pd.merge(asstdf,instdf, how="left")

    return (asstdf, instdf, joindf)


############################################################################
# %%
# Define frame filter and projection functions

def filterproj_main( asstdf ):

    cols = ["asset_id", "sonyci_id", "media_type", "asset_type", "level_of_user_access", "broadcast_date", "created_date", "consolidated_title", "proxy_duration"]
    return( asstdf[ cols ] ) 



############################################################################
# %%
# Define functions for I/O -- reading parameters and writing out results
def write_csv( df, csv_filename: str ):
    # write out selected and projected dataframe to CSV

    df.to_csv(csv_filename, index=False)


############################################################################
def main():
    
    parser = parser = argparse.ArgumentParser(
        prog='framify.py',
        description='routines for working with AAPB PBcore in Pandas Dataframes',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("pbcore_dir", metavar="DIR", nargs="?",
        help="Path to directory containing PBCore XML files")
    parser.add_argument("batch_csv", metavar="OUTPUT", nargs="?",
        help="Path of the CSV file to define a batch")

    args = parser.parse_args() 

    if args.pbcore_dir is not None:
        pbcore_dir = args.pbcore_dir
    else:
        print("Error: No DIR supplied.  Run with -h for help.")
    
    if args.batch_csv is not None:
        batch_csv = args.batch_csv
    else:
        print("Error: No OUTPUT supplied.  Run with -h for help.")

    assttbl, insttbl = tablify( pbcore_dir )
    asstdf, instdf, joindf = inframe( assttbl, insttbl )
    projected = filterproj_main( asstdf )

    write_csv( projected, batch_csv )




# %%
# Execute 
if __name__ == "__main__":
    main()

