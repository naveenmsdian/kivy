import streamlit as st
import os
import shutil
from pathlib import Path
import subprocess

# Streamlit UI
st.title("Kivy to Android APK Converter")

st.markdown("""
This application helps you convert your Kivy Python project into an Android APK.
Upload your Kivy project folder as a zip file, and we'll handle the rest.
""")

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

        # Display a link to download the build log
        st.write("You can download the full build log here:")
        with open(log_file, "rb") as f:
            st.download_button("Download Build Log", f, "build_output.log")
