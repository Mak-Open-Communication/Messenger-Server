FIRST_START=true
SETUP_MAIN=true
SETUP_MEDIA=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-main)
            SETUP_MAIN=false
            shift
            ;;
        --no-media)
            SETUP_MEDIA=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--no-main] [--no-media]"
            exit 1
            ;;
    esac
done

if [ "$SETUP_MAIN" = "false" ] && [ "$SETUP_MEDIA" = "false" ]; then
    echo ""
    echo " Error: Cannot disable both Main and Media servers!"
    echo " At least one server must be enabled."
    echo ""
    exit 1
fi

if [ "$FIRST_START" = "true" ]; then
    echo ""
    echo " The server is set up with:"
    echo "  PostgreSQL"

    if [ "$SETUP_MAIN" = "true" ]; then
        echo "  Main Server"
    fi

    if [ "$SETUP_MEDIA" = "true" ]; then
        echo "  Media Server"
    fi

    echo ""
    echo " Please, configure '.env' to your requirements and restart the server."

    echo ""
else
    echo "Not first run"
fi