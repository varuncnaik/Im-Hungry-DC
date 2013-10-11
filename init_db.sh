mkdir -p tmp
touch tmp/caldining.db
python -c "from caldining import init_db; init_db()"
