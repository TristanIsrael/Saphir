class ViewerConstants():

    # Office calc formats
    CALC_EXTENTIONS = [
        "*.ods", "*.ots",
        "*.xls", "*.xlsx", "*.xlsm", "*.xlsb",
        "*.xlt", "*.xltx", "*.xltm",
        "*.csv", "*.tsv", "*.tab", "*.dif",
        "*.dbf",
        "*.wk1", "*.wk3", "*.wk4", "*.wks", "*.123", "*.pxl",
        "*.gnumeric"
    ]

    # Office text formats
    WRITER_EXTENSIONS = [
        "*.odt", "*.ott",
        "*.doc", "*.docx", "*.docm",
        "*.dot", "*.dotx", "*.dotm",
        "*.epub", "*.fb2",
        "*.wpd", "*.abw", "*.sdw"
    ]

    # Images
    IMAGES_EXTENSIONS = [
        "*.bmp",
        "*.gif",
        "*.jpg", "*.jpeg",
        "*.png",
        "*.pbm", "*.pgm", "*.ppm",
        "*.xbm", "*.xpm",
        "*.tiff", "*.tif",
        "*.heif", "*.heic"
    ]

    # Videos
    VIDEOS_EXTENSIONS = [
        "*.mp4", "*.m4v",
        "*.mkv",
        "*.avi",
        "*.mov",
        "*.wmv",
        "*.flv",
        "*.webm",
        "*.mpg", "*.mpeg",
        "*.3gp", "*.3g2",
        "*.ts", "*.mts", "*.m2ts"
    ]

    # Audio
    AUDIO_EXTENSIONS = [
        "*.mp3",
        "*.wav",
        "*.aac",
        "*.flac",
        "*.ogg",
        "*.m4a",
        "*.wma"
    ]

    FILES_FILTERS = list(set(
        CALC_EXTENTIONS + WRITER_EXTENSIONS + IMAGES_EXTENSIONS + VIDEOS_EXTENSIONS + AUDIO_EXTENSIONS
    ))
