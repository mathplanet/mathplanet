# Write your MySQL query statement below
SELECT MAX(salary) as SecondHighestSalary
From Employee
WHERE Salary < (SELECT MAX(Salary) FROM Employee);