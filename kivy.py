import streamlit as st
import os
import shutil
from pathlib import Path
import subprocess

# Function to check if a command is available on the system
def is_command_available(command):
    return shutil.which(command) is not None

# Streamlit UI
st.title("Kivy to Android APK Converter")

st.markdown("""
This application helps you convert your Kivy Python project into an Android APK.
Upload your Kivy project folder as a zip file, and we'll handle the rest.
""")

# Check for required system dependencies
missing_dependencies = []

# Check for zlib1g-dev (required for zlib headers)
if not shutil.which("zlib1g-dev"):
    try:
        # On Linux, we can check if zlib headers are installed
        result = subprocess.run(["dpkg", "-s", "zlib1g-dev"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            missing_dependencies.append("zlib1g-dev (run: sudo apt-get install zlib1g-dev)")
    except FileNotFoundError:
        missing_dependencies.append("zlib1g-dev (run: sudo apt-get install zlib1g-dev)")

# Check for Java JDK
if not is_command_available("javac"):
    missing_dependencies.append("Java JDK (install from: https://www.oracle.com/java/technologies/javase-jdk11-downloads.html)")

# Check for Android SDK
if not os.environ.get("ANDROID_HOME") or not Path(os.environ["ANDROID_HOME"]).exists():
    missing_dependencies.append("Android SDK (set ANDROID_HOME environment variable and install from: https://developer.android.com/studio)")

# Check for Android NDK
if not os.environ.get("ANDROID_NDK_HOME") or not Path(os.environ["ANDROID_NDK_HOME"]).exists():
    missing_dependencies.append("Android NDK (set ANDROID_NDK_HOME environment variable and install from: https://developer.android.com/ndk/downloads)")

# Display missing dependencies
if missing_dependencies:
    st.error("The following dependencies are missing:")
    for dep in missing_dependencies:
        st.write(dep)
    st.stop()

# Upload the Kivy project as a zip file
uploaded_file = st.file_uploader("Upload Kivy project zip file", type="zip")

if uploaded_file:
    # Define paths
    project_dir = Path("kivy_project")
    build_dir = project_dir / ".buildozer"
    apk_dir = build_dir / "android" / "platform" / "build" / "outputs" / "apk"

    # Clear previous builds
    if project_dir.exists():
        shutil.rmtree(project_dir)

    # Create project directory
    project_dir.mkdir(parents=True, exist_ok=True)

    # Save the uploaded file
    zip_path = project_dir / "project.zip"
    with open(zip_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Extract the zip file
    shutil.unpack_archive(zip_path, project_dir)

    st.success("Project uploaded and extracted successfully!")

    # Check for buildozer.spec or create it if not present
    spec_file = project_dir / "buildozer.spec"
    if not spec_file.exists():
        st.warning("buildozer.spec not found. Creating a default one.")
        subprocess.run(["buildozer", "init"], cwd=project_dir)
    else:
        st.info("Found existing buildozer.spec.")

    # Display content of buildozer.spec for user to review
    with open(spec_file, "r") as f:
        spec_content = f.read()

    st.text_area("buildozer.spec content:", spec_content, height=300)

    # Button to start building the APK
    if st.button("Build APK"):
        st.write("Starting APK build process...")

        # Run buildozer command to build APK
        build_command = "buildozer -v android debug"
        process = subprocess.Popen(build_command.split(), cwd=project_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        with st.spinner('Building APK...'):
            build_output = ""
            for line in iter(process.stdout.readline, ''):
                build_output += line
                st.text(line.strip())

            stdout, stderr = process.communicate()
            
            # Write full logs to a temporary file
            log_file = project_dir / "build_output.log"
            with open(log_file, "w") as f:
                f.write(build_output)
                f.write("\nStandard Error:\n")
                f.write(stderr)

            if process.returncode == 0:
                st.success("APK build completed successfully!")
                # Locate the built APK
                apk_files = list(apk_dir.glob("*.apk"))
                if apk_files:
                    apk_path = apk_files[0]
                    st.write(f"APK generated: {apk_path.name}")
                    with open(apk_path, "rb") as apk_file:
                        st.download_button(
                            label="Download APK",
                            data=apk_file,
                            file_name=apk_path.name,
                            mime="application/vnd.android.package-archive"
                        )
                else:
                    st.error("No APK file found in the build output.")
            else:
                st.error("APK build failed. Check the build logs for more details.")
                st.error(stderr)
                st.write("You can download the full build log here:")
                with open(log_file, "rb") as f:
                    st.download_button("Download Build Log", f, "build_output.log")
