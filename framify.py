
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
# Helper functions
def get_el_text( e ):

    text = ""
    if e is not None:
        if e.text is not None:
            text = e.text.strip()

    return text


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
        print("Warning: Specified directory includes files with extension other than .xml")
        print("         or perhaps a file named simply '.xml'.")
    
    print("Will attempt to framify", len(filenames), "files...")

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
        aapb_pbcore_id = get_el_text(e)
        asset_id = aapb_pbcore_id.replace('/', '-').replace('_', '-')

        # Asset.sonyci_id
        # Takes the Sony Ci ID from the first non-empty matching element
        att = "[@source='Sony Ci']"
        es = root.findall("pbcore:pbcoreIdentifier"+att,ns)
        sonyci_id = ""
        for e in es:
            if (not sonyci_id and e.text):
                sonyci_id = e.text.strip()

        # Asset.local_identifer, Asset.pbs_nola_code, Asset.eidr_id, etc
        other_id_1 = other_id_2 = other_id_3 = ""
        es = root.findall("pbcore:pbcoreIdentifier",ns)
        for e in es:
            if e.attrib["source"] not in ["http://americanarchiveinventory.org", "Sony Ci"]:
                other_id = e.attrib["source"] + ":" + get_el_text(e)
                if not other_id_1:
                    other_id_1 = other_id
                elif not other_id_2:
                    other_id_2 = other_id
                elif not other_id_3:
                    other_id_3 = other_id


        #
        # Annotation elements 
        #
        # Asset.organization
        att = "[@annotationType='organization']"
        e = root.find("pbcore:pbcoreAnnotation"+att,ns)
        contributing_organization = get_el_text(e)

        # Asset.level_of_user_access
        att = "[@annotationType='Level of User Access']"
        e = root.find("pbcore:pbcoreAnnotation"+att,ns)
        level_of_user_access = get_el_text(e)

        # Asset.special_collections
        # handling multiple values
        att = "[@annotationType='special_collections']"
        es = root.findall("pbcore:pbcoreAnnotation"+att,ns)
        tlist = [ get_el_text(e) for e in es ]
        special_collections = ','.join(tlist)

        # Asset.transcript_status
        att = "[@annotationType='Transcript Status']"
        e = root.find("pbcore:pbcoreAnnotation"+att,ns)
        transcript_status = get_el_text(e)

        # Asset.transcript_url
        att = "[@annotationType='Transcript URL']"
        e = root.find("pbcore:pbcoreAnnotation"+att,ns)
        transcript_url = get_el_text(e)

        # Proxy Start Time
        att = "[@annotationType='Proxy Start Time']"
        e = root.find("pbcore:pbcoreAnnotation"+att,ns)
        proxy_start_time = get_el_text(e)

        #
        # Date elements 
        #
        # Asset.broadcast_date
        att = "[@dateType='Broadcast']"
        e = root.find("pbcore:pbcoreAssetDate"+att,ns)
        broadcast_date = get_el_text(e)

        # Asset.created_date
        att = "[@dateType='Created']"
        e = root.find("pbcore:pbcoreAssetDate"+att,ns)
        created_date = get_el_text(e)

        # Asset.copyright_date
        att = "[@dateType='Copyright']"
        e = root.find("pbcore:pbcoreAssetDate"+att,ns)
        copyright_date = get_el_text(e)

        # Asset.date (no @dateType)
        es = root.findall("pbcore:pbcoreAssetDate",ns)
        esnoat = [e for e in es if 'dateType' not in e.attrib]  
        date = get_el_text(esnoat[0]) if len(esnoat) > 0 else ""

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
        series_title = get_el_text(e)

        # Asset.program_title
        att = "[@titleType='Program']"
        e = root.find("pbcore:pbcoreTitle"+att,ns)
        program_title = get_el_text(e)

        # Asset.episode_title
        att = "[@titleType='Episode']"
        e = root.find("pbcore:pbcoreTitle"+att,ns)
        episode_title = get_el_text(e)

        # Asset.episode_number
        att = "[@titleType='Episode Number']"
        e = root.find("pbcore:pbcoreTitle"+att,ns)
        episode_number = get_el_text(e)

        # Asset.segment_title
        att = "[@titleType='Segment']"
        e = root.find("pbcore:pbcoreTitle"+att,ns)
        segment_title = get_el_text(e)

        # Asset.raw_footage_title
        att = "[@titleType='Raw Footage']"
        e = root.find("pbcore:pbcoreTitle"+att,ns)
        raw_footage_title = get_el_text(e)

        # Asset.promo_title
        att = "[@titleType='Promo']"
        e = root.find("pbcore:pbcoreTitle"+att,ns)
        promo_title = get_el_text(e)

        # Asset.clip_title
        att = "[@titleType='Clip']"
        e = root.find("pbcore:pbcoreTitle"+att,ns)
        clip_title = get_el_text(e)

        # Asset.title (no @titleType)
        es = root.findall("pbcore:pbcoreTitle",ns)
        esnoat = [e for e in es if 'titleType' not in e.attrib]
        title = get_el_text(esnoat[0]) if len(esnoat) > 0 else ""

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
                consolidated_title = title

        #
        # Description elements 
        #
        # Asset.series_description
        att = "[@descriptionType='Series']"
        e = root.find("pbcore:pbcoreDescription"+att,ns)
        series_description = get_el_text(e)

        # Asset.program_description
        att = "[@descriptionType='Program']"
        e = root.find("pbcore:pbcoreDescription"+att,ns)
        program_description = get_el_text(e)

        # Asset.episode_description
        att = "[@descriptionType='Episode']"
        e = root.find("pbcore:pbcoreDescription"+att,ns)
        episode_description = get_el_text(e)

        # Asset.segment_description
        att = "[@descriptionType='Segment']"
        e = root.find("pbcore:pbcoreDescription"+att,ns)
        segment_description = get_el_text(e)

        # Asset.raw_footage_description
        att = "[@descriptionType='Raw Footage']"
        e = root.find("pbcore:pbcoreDescription"+att,ns)
        raw_footage_description = get_el_text(e)

        # Asset.promo_description
        att = "[@descriptionType='Promo']"
        e = root.find("pbcore:pbcoreDescription"+att,ns)
        promo_description = get_el_text(e)

        # Asset.clip_description
        att = "[@descriptionType='Clip']"
        e = root.find("pbcore:pbcoreDescription"+att,ns)
        clip_description = get_el_text(e)

        # Asset.description (no @descriptionType)
        es = root.findall("pbcore:pbcoreDescription",ns)
        esnoat = [e for e in es if 'descriptionType' not in e.attrib]
        description = get_el_text(esnoat[0]) if len(esnoat) > 0 else ""

        # Canonical description
        # Build a single canonical description, given that there might be several
        # descriptions associated with the asset
        consolidated_description = ""
        if series_description:
            consolidated_description += (series_description + ": ")
        consolidated_description += episode_description
        consolidated_description += program_description
        consolidated_description += segment_description
        consolidated_description += raw_footage_description
        consolidated_description += promo_description
        consolidated_description += clip_description
        if description:
            if consolidated_description:
                consolidated_description += (" " + description)
            else:
                consolidated_description = description

        #
        # Other elements 
        #
        # Asset.asset_types
        att = ""
        e = root.find("pbcore:pbcoreAssetType"+att,ns)
        asset_type = get_el_text(e)


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
            crole = get_el_text(crole_e)
            creator_e = pbcreator_e.find("pbcore:creator",ns)
            creator = get_el_text(creator_e)
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
                    dig_mts.append(get_el_text(mte))
                elif inst.find("pbcore:instantiationPhysical",ns) is not None:
                    phs_mts.append(get_el_text(mte))
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
                    if ( get_el_text(e) == "Proxy" ):
                        e = inst.find("pbcore:instantiationDuration",ns)
                        if e is not None:
                            proxy_duration = get_el_text(e)


        # Instantiation records
        insts = root.findall(".//pbcore:pbcoreInstantiation",ns)
        for inst in insts:

            # Instantiation identifers
            # handling multiple values by concatenating all of them into a |-separated list
            att = ""
            es = inst.findall("pbcore:instantiationIdentifier",ns)
            tlist = [ get_el_text(e) for e in es ]
            inst_identifiers = '|'.join(tlist)

            # Instantiation media type
            att = ""
            e = inst.find("pbcore:instantiationMediaType"+att,ns)
            inst_media_type = get_el_text(e)

            # Instantiation date
            att = ""
            e = inst.find("pbcore:instantiationDate"+att,ns)
            inst_date = get_el_text(e)

            # Instantiation digital format
            att = ""
            e = inst.find("pbcore:instantiationDigital"+att,ns)
            inst_digital_format = get_el_text(e)

            # Instantiation physical format
            att = ""
            e = inst.find("pbcore:instantiationPhysical"+att,ns)
            inst_physical_format = get_el_text(e)

            # Instantiation generations
            att = ""
            e = inst.find("pbcore:instantiationGenerations"+att,ns)
            inst_generations = get_el_text(e)

            # Instantiation duration
            att = ""
            e = inst.find("pbcore:instantiationDuration"+att,ns)
            inst_duration = get_el_text(e)

            # Instantiation location
            att = ""
            e = inst.find("pbcore:instantiationLocation"+att,ns)
            inst_location = get_el_text(e)

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
                        other_id_1,
                        other_id_2,
                        other_id_3,
                        media_type,
                        asset_type, 
                        contributing_organization,
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
                        series_description,
                        program_description,
                        episode_description,
                        segment_description,
                        raw_footage_description,
                        promo_description,
                        clip_description,
                        description,
                        consolidated_description,
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
                "other_id_1",
                "other_id_2",
                "other_id_3",
                "media_type",
                "asset_type", 
                "contributing_organization",
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
                "series_description",
                "program_description",
                "episode_description",
                "segment_description",
                "raw_footage_description",
                "promo_description",
                "clip_description",
                "description",
                "consolidated_description",
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

    cols = ["asset_id", 
            "sonyci_id", 
            "media_type", 
            "asset_type", 
            "level_of_user_access", 
            "broadcast_date", 
            "created_date",
            "producing_organization", 
            "contributing_organization",
            "consolidated_title"] 
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
    
    parser.add_argument("-a", "--allcols", action="store_true",
        help="Include all inframed columns, not just default columns")
    parser.add_argument("pbcore_dir", metavar="DIR", nargs="?",
        help="Path to directory containing PBCore XML files")
    parser.add_argument("batch_csv", metavar="OUTPUT", nargs="?",
        help="Path of the CSV file to define a batch")

    args = parser.parse_args() 

    args_ok = True

    if args.pbcore_dir is not None:
        pbcore_dir = args.pbcore_dir
        if not os.path.exists(pbcore_dir):
            print("Error: Specified directory does not exist.  Run with -h for help.")
            args_ok = False
    else:
        print("Error: No DIR supplied.  Run with -h for help.")
        args_ok = False
    
    if args.batch_csv is not None:
        batch_csv = args.batch_csv
    else:
        print("Error: No OUTPUT supplied.  Run with -h for help.")
        args_ok = False

    if args_ok:
        assttbl, insttbl = tablify( pbcore_dir )
        asstdf, instdf, joindf = inframe( assttbl, insttbl )
        
        if args.allcols:
            projected = asstdf
        else:
            projected = filterproj_main( asstdf )

        print("PBCore XML files framified.")
        print("Will write CSV file:", batch_csv)
        write_csv( projected, batch_csv )
        print("Done.")




# %%
# Execute 
if __name__ == "__main__":
    main()

