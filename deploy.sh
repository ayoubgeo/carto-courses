#!/bin/bash
# deploy.sh - runs on cPanel server via cron job at 8:00 AM daily
# Pulls latest courses from GitHub and copies to public_html

REPO="/home2/cartoma/courses-repo"
PUBLIC="/home2/cartoma/public_html"
LOG="/home2/cartoma/deploy.log"

echo "========================================" >> $LOG
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deploy started" >> $LOG

# Pull latest from GitHub
cd $REPO
git pull origin main >> $LOG 2>&1

# Copy new course HTML files to public_html/courses/
mkdir -p $PUBLIC/courses
cp -u $REPO/courses/*.html $PUBLIC/courses/ 2>/dev/null && echo "Courses copied." >> $LOG

# Copy updated index page
cp -u $REPO/geoaicourses.html $PUBLIC/geoaicourses.html 2>/dev/null && echo "Index updated." >> $LOG

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deploy done." >> $LOG
echo "========================================" >> $LOG
