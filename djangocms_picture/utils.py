from cms.models import CMSPlugin
from cmsplugin_filer_image.models import FilerImage
from djangocms_picture.models import Picture

def migrateImage(old_plugin):
    old_plugin = old_plugin.get_bound_plugin()
    
    link = ''
    # priority was free_link > page_link > file_link > original file
    if not old_plugin.free_link and old_plugin.file_link:
        link = old_plugin.file_link.url
    elif not old_plugin.free_link and old_plugin.original_link:
        if old_plugin.image:
            link = old_plugin.image.url
        else:
            link = old_plugin.image_url
    
    new_plugin = Picture(
        language = old_plugin.language,
        parent = old_plugin.parent,
        placeholder = old_plugin.placeholder,
        position = old_plugin.position,
        plugin_type = 'PicturePlugin',

        # copy fields
        template = 'default',
        # attributes = '',
        picture = old_plugin.image,
        external_picture = old_plugin.image_url or '',
        width = old_plugin.width,
        height = old_plugin.height,
        alignment = old_plugin.alignment or '',
        caption_text = old_plugin.caption_text or '',
        link_url = link,
        link_page = old_plugin.page_link,
        link_target = '_blank' or '',
        link_attributes = old_plugin.link_attributes,
        use_automatic_scaling = old_plugin.use_autoscale,
        use_no_cropping = old_plugin.use_original_image,
        use_crop = old_plugin.crop,
        use_upscale = old_plugin.upscale,
        thumbnail_options = old_plugin.thumbnail_option,
        
        # style, # use attributes instead
        # alt_text, # not used
    )

    # insert new plugin into tree at original position, shifting original to right
    new_plugin = old_plugin.add_sibling(pos='left', instance=new_plugin)
    
    # new_plugin.copy_relations(old_plugin)
    new_plugin.post_copy(old_plugin, [(new_plugin, old_plugin),])
    
    # in case this is a child of a TextPlugin that needs
    # its content updated with the newly copied plugin
    plugin_replacements = []
    parent = new_plugin.parent
    if parent:
        # we need a complete list of (new, old) plugin pairs
        # for all children, not just the one we are replacing,
        # otherwise all plugin references will get blanked out
        # in TextPlugins
        parent = parent.get_bound_plugin();
        for child in parent.get_children():
            if child.pk != new_plugin.pk:
                if child.pk == old_plugin.pk:
                    replacement = new_plugin # use the new plugin instead of old
                else:
                    replacement = child # keep this as is
                plugin_replacements.append((replacement, child))
        parent.post_copy(parent, plugin_replacements)
        
    old_plugin.delete()

    return new_plugin

def convert_filer_to_djangocms_picture():
    qs = FilerImage.objects.all()
    for image in qs:
        new_plugin = migrateImage(image)