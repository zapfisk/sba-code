#!/usr/bin/env python

from gimpfu import *
import csv

def save_grad_certificates(image, layer, output_folder, team_output_folder, season_roster_file, restrictions, do_export):
    ''' Create and export graduation certificates for the SBA.
    
    Parameters
    ----------
    image : image
        The current image.
    layer : gimp.Layer
        Selected layer (unused, but required afaik).
    outputFolder : str
        The folder in which to save the images.
    seasonRosters : str
        The contents of the csv file of the academy roster sheet.
    export : bool
        If false, do not export any images (can be used to generate the list of missing signatures faster)
    '''
    # Indicates that the process has started.
    gimp.progress_init("Creating Graduation Certificates...")
    # Set up an undo group, so the operation will be undone in one step.
    pdb.gimp_image_undo_group_start(image)

    # convert csv to teams
    teams = get_teams(season_roster_file)

    try:
        main_name = pdb.gimp_image_get_layer_by_name(image, "main_name")
        main_team = pdb.gimp_image_get_layer_by_name(image, "main_team")
        main_mates = pdb.gimp_image_get_layer_by_name(image, "main_mates")
        text_team = pdb.gimp_image_get_layer_by_name(image, "text_team")
        text_mates = pdb.gimp_image_get_layer_by_name(image, "text_mates")
        main_award = pdb.gimp_image_get_layer_by_name(image, "main_award")
        text_roster = pdb.gimp_image_get_layer_by_name(image, "text_roster")

        mid = pdb.gimp_image_width(image) / 2
    except:
        gimp.message("At least one main layer does not exist." \
        " Make sure to call this plug-in on the correct file.")

    for t in teams:
        # if restrictions are set, skip all teams that do not match the string
        if (restrictions != '' and restrictions != t.name):
            continue
        
        # set coach and manager signature layer active
        set_signatures_active(image, t, True)
        
        # if setting is on, only collect missing signatures and then continue, do not call anything to do with exporting
        if (not do_export):
            set_signatures_active(image, t, False)
            continue

        # set text for team name
        pdb.gimp_text_layer_set_text(main_team, t.name)
        # readjust position to be centered
        center_text(mid, [text_team, main_team])

        # prepare team certificates
        pdb.gimp_text_layer_set_text(main_award, "Awarded to the team")
        pdb.gimp_item_set_visible(text_mates, False)
        pdb.gimp_item_set_visible(text_team, False)
        pdb.gimp_item_set_visible(main_team, False)
        pdb.gimp_item_set_visible(text_roster, True)

        # set team name and list team mates
        pdb.gimp_text_layer_set_text(main_name, t.name)
        pdb.gimp_text_layer_set_text(main_mates, get_teammates(t.players, None))
        # readjust position to be centered
        center_text(mid, [main_mates])

        # export team certificate
        export(image, team_output_folder, t.name)

        # prepare player certificates
        pdb.gimp_text_layer_set_text(main_award, "Awarded to")
        pdb.gimp_item_set_visible(text_mates, True)
        pdb.gimp_item_set_visible(text_team, True)
        pdb.gimp_item_set_visible(main_team, True)
        pdb.gimp_item_set_visible(text_roster, False)

        for player in t.players:
            pdb.gimp_text_layer_set_text(main_name, player) # set player name
            pdb.gimp_text_layer_set_text(main_mates, get_teammates(t.players, player)) # set all other names on team 
            center_text(mid, [text_mates, main_mates]) # readjust position to be centered
            export(image, output_folder, t.name + "_" + player)

        # set coach and manager signature layer inactive
        set_signatures_active(image, t, False)

    # List Missing Signatures
    gimp.message("Missing Signatures from " + str(missing_signs))

    # Close the undo group.
    pdb.gimp_image_undo_group_end(image)
    # End progress.
    pdb.gimp_progress_end()

def center_text(mid, texts):
    ''' Horizontally centers different text fields that are next to each other.

    Parameters
    ----------
    mid : int
        The middle of the image hozirontally in pixels (half of the image width).
    mains : list[gimp.Layer]
        List of text layers to be centered, in order from left to right.
    '''
    sum = 0
    for text in texts: 
        sum += text.width

    x_text = mid - (sum / 2)
    for text in texts:
        _, y_text = text.offsets
        text.set_offsets(x_text, y_text)
        x_text += text.width

def get_teammates(players, player):
    ''' Formats a list of players into a string in the format "{p(1)}, {p(2)}, [...], {p(n-1)} and {p(n)}."

    Parameters
    ----------
    players : list[str]
        The list of player names to be formatted.
    player : str
        Player to be left out of the formatted string.

    Returns
    -------
    str
        String of players in the format "{p(1)}, {p(2)}, [...], {p(n-1)} and {p(n)}."
    '''
    ps = list(players) # create a copy to avoid side effects
    if (player != None): 
        ps.remove(player)
    last = ps[-1]
    ps.pop() # remove last

    val = ""
    for p in ps:
        val += p + ", "
    
    return val[:-2] + " and " + last + "."

# stores every mentor whose signature wasn't found in the file
missing_signs = []

def set_signatures_active(image, team, active):
    ''' Sets signatures for team managers and coaches active, as well as the correct underscoring and labeling of the signatures.

    Parameters
    ----------
    image : gimp.Image
        Reference to the image that the script is being called on.
    team : Team
        Team for which to set signatures active.
    active : bool
        If true, set signatures active, if false, hide them.
    '''
    try:
        main_manager = pdb.gimp_image_get_layer_by_name(image, "main_manager")
        main_coach = pdb.gimp_image_get_layer_by_name(image, "main_coach")
        main_manager_coach = pdb.gimp_image_get_layer_by_name(image, "main_manager_coach")
    except:
        gimp.message("At least one main layer does not exist. Make sure to call this plug-in on the correct file.")

    pdb.gimp_item_set_visible(main_manager, not team.shared_responsibility)
    pdb.gimp_item_set_visible(main_coach, not team.shared_responsibility)
    pdb.gimp_item_set_visible(main_manager_coach, team.shared_responsibility)
    if (not team.shared_responsibility):
        pdb.gimp_text_layer_set_text(main_coach, "Coach" if not team.mult_coaches else "Coaches")
        pdb.gimp_text_layer_set_text(main_manager, "Team Manager" if not team.mult_managers else "Team Managers")

    for mentor in team.mentors:
        if (mentor == ""):
            continue

        layer = pdb.gimp_image_get_layer_by_name(image, mentor)
        if (layer != None):
            pdb.gimp_item_set_visible(layer, active)
        elif active: # since this function gets called twice, only append list of missing mentor once
            missing_signs.append(mentor)


def export(image, outputFolder, name):
    ''' Export the image to png.

    Parameters
    ----------
    image : gimp.Image
        Reference to the image that the script is being called on.
    outputFolder : str
        The folder to write to.
    name : str
        The name of the file to be created.
    '''
    name = name.translate(None, '/\!?@#$.:,;<>\"\'`*+~{([])}') # remove special characters

    try:
        # Save as PNG by creating new temporary image, merging all layers, exporting, and deleting temp image.
        new_image = pdb.gimp_image_duplicate(image)
        layer = pdb.gimp_image_merge_visible_layers(new_image, CLIP_TO_IMAGE)
        gimp.pdb.file_png_save(image, layer, outputFolder + "\\" + name + ".png", "raw_filename", 0, 9, 0, 0, 0, 0, 0)
        pdb.gimp_image_delete(new_image)
    except Exception as err:
        gimp.message("Unexpected error: " + str(err))

class Team:
    ''' Class to store information about academy teams.
    '''
    name = ""
    players = []
    mentors = []
    shared_responsibility = False
    mult_coaches = False
    mult_managers = False

    def __init__(self, name="", players=[], mentors=[], shared_responsibility=False, mult_coaches=False, mult_managers=False):
        self.name = name
        self.players = players
        self.mentors = mentors
        self.shared_responsibility = shared_responsibility
        self.mult_coaches = mult_coaches
        self.mult_managers = mult_managers
    def type_to_str(self):
        if (self.shared_responsibility):
            return "Shared Responsibility"
        if (self.mult_coaches and self.mult_managers):
            return "Multiple Both"
        if (self.mult_coaches):
            return "Multiple Coaches"
        if (self.mult_managers):
            return "Multiple Managers"
        return "Normal"
    def __str__(self):
        return self.name + ", " + str(self.players) + ", " + str(self.mentors) + ", (" + Team.type_to_str(self) + ")"

def get_teams(season_file):
    ''' Convert the contents of the academy roster sheet csv file into a usable format.

    Parameters
    ----------
    season_file : str
        File path of the csv file of the page of the current season of academy roster history sheet.
    '''

    with open(season_file, mode ='r') as file:
        r = csv.reader(file)
        r.next() # skip header line

        teams = []
        for team in r:
            players = [team[i].strip() for i in range(4, 9)] # players are at IDs 4 to 8 (inclusive)
            players = [x for x in players if x != ''] # remove empty strings (for 4 player teams)

            coaches = team[9].split(' & ') # coaches are at ID 9
            managers = team[10].split(' & ') # team managers are at ID 10

            t = Team(name = team[0], # team name is at ID 0
                    players = players, 
                    mentors = coaches + managers,
                    shared_responsibility = False, # TODO: implement this based on input field
                    mult_coaches = len(coaches) > 1,
                    mult_managers = len(managers) > 1)
            
            teams.append(t)

        return teams

register(
    "python_fu_create_grad_certificates",
    "Graduation Certificates",
    "Create and export graduation certificates for the Stronghold Beginners Academy.",
    "Fisk @zapfisk.splstrong.com",
    "GNU Lesser General Public License v2.1",
    "2025",
    "<Image>/Filters/SplStrong/Graduation Certificates",
    "*",
    [
        (PF_DIRNAME, "output_folder", "Player Output directory", ""),
        (PF_DIRNAME, "team_output_folder", "Team Output directory", ""),
        (PF_FILENAME, "season_roster_file", "file path of the academy roster sheet csv file", ""),
        (PF_STRING, "restrictions", "restrict export to one team by team name", ""),
        (PF_BOOL, "do_export", "export\n(set false to just get missing signatures)", True),
    ],
    [],
    save_grad_certificates)

main()

