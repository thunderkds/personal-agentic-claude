Self-hosted fonts for the Easy Kit site (T204).

Family            Weights        Source package                  Version  License
IBM Plex Sans     400 500 600    @fontsource/ibm-plex-sans       5.3.0    SIL OFL 1.1
IBM Plex Mono     400 500        @fontsource/ibm-plex-mono       5.3.0    SIL OFL 1.1

Only the "latin" subset, normal style, woff2 files are kept. The license text is in OFL.txt.

How the files were fetched (outside the repo, no node_modules committed):
  npm pack @fontsource/ibm-plex-sans@5.3.0 @fontsource/ibm-plex-mono@5.3.0
  copy package/files/ibm-plex-{sans,mono}-latin-<weight>-normal.woff2 and package/LICENSE
