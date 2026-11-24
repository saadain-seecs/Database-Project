// MongoDB (mongosh) version of the main reports.  Week 15: SQL vs NoSQL
// Load first:  mongoimport --db pharmacy_nosql --collection sales    --jsonArray --file sales.json
//              mongoimport --db pharmacy_nosql --collection products  --jsonArray --file products.json
//              mongoimport --db pharmacy_nosql --collection customers --jsonArray --file customers.json
// Then:        mongosh pharmacy_nosql mongo_queries.js

// Indexes that mirror the relational ones
db.sales.createIndex({ sale_date: 1 });
db.sales.createIndex({ 'customer.customer_id': 1 });
db.products.createIndex({ 'category.category_id': 1 });
db.products.createIndex({ 'batches.expiry_date': 1 });

// A sale is ONE document (bill + items + customer snapshot): no JOIN is needed to print a bill
printjson(db.sales.findOne({ _id: 40 }));

// Q5  monthly sales  (SQL: GROUP BY month)
printjson(db.sales.aggregate([
  {
    "$group": {
      "_id": {
        "$substr": [
          "$sale_date",
          0,
          7
        ]
      },
      "bills": {
        "$sum": 1
      },
      "revenue": {
        "$sum": "$total_amount"
      }
    }
  },
  {
    "$sort": {
      "_id": 1
    }
  }
]).toArray());

// Q6  top 10 best-selling medicines  (SQL: GROUP BY product ... LIMIT 10)
printjson(db.sales.aggregate([
  {
    "$unwind": "$items"
  },
  {
    "$group": {
      "_id": "$items.name",
      "units_sold": {
        "$sum": "$items.qty"
      },
      "revenue": {
        "$sum": "$items.line_total"
      }
    }
  },
  {
    "$sort": {
      "units_sold": -1,
      "revenue": -1
    }
  },
  {
    "$limit": 10
  }
]).toArray());

// Q8  customers with highest spending  (SQL: GROUP BY ... HAVING)
printjson(db.sales.aggregate([
  {
    "$group": {
      "_id": {
        "id": "$customer.customer_id",
        "name": "$customer.name"
      },
      "bills": {
        "$sum": 1
      },
      "total_spent": {
        "$sum": "$total_amount"
      }
    }
  },
  {
    "$match": {
      "total_spent": {
        "$gte": 2000
      }
    }
  },
  {
    "$sort": {
      "total_spent": -1
    }
  },
  {
    "$limit": 10
  }
]).toArray());

// Q11 revenue per category  (SQL: 4-table JOIN + GROUP BY)
printjson(db.sales.aggregate([
  {
    "$unwind": "$items"
  },
  {
    "$group": {
      "_id": "$items.category",
      "units_sold": {
        "$sum": "$items.qty"
      },
      "revenue": {
        "$sum": "$items.line_total"
      }
    }
  },
  {
    "$sort": {
      "revenue": -1
    }
  }
]).toArray());

// Q9  products below reorder level  (SQL: correlated sub-query)
printjson(db.products.aggregate([
  {
    "$project": {
      "name": 1,
      "reorder_level": 1,
      "on_hand": {
        "$sum": {
          "$map": {
            "input": {
              "$filter": {
                "input": "$batches",
                "as": "b",
                "cond": {
                  "$gte": [
                    "$$b.expiry_date",
                    "2026-11-18"
                  ]
                }
              }
            },
            "as": "x",
            "in": "$$x.qty"
          }
        }
      }
    }
  },
  {
    "$project": {
      "name": 1,
      "on_hand": 1,
      "reorder_level": 1,
      "low": {
        "$lt": [
          "$on_hand",
          "$reorder_level"
        ]
      }
    }
  },
  {
    "$match": {
      "low": true
    }
  },
  {
    "$sort": {
      "name": 1
    }
  }
]).toArray());

// Transaction across two collections is possible only on a replica set / sharded cluster:
// const s = db.getMongo().startSession(); s.startTransaction(); /* insert sale + update product batches */ s.commitTransaction();
