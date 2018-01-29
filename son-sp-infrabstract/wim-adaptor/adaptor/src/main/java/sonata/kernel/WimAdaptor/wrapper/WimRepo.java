/**
 * Copyright (c) 2015 SONATA-NFV, UCL, NOKIA, NCSR Demokritos ALL RIGHTS RESERVED.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software distributed under the License
 * is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
 * or implied. See the License for the specific language governing permissions and limitations under
 * the License.
 * 
 * Neither the name of the SONATA-NFV, UCL, NOKIA, NCSR Demokritos nor the names of its contributors
 * may be used to endorse or promote products derived from this software without specific prior
 * written permission.
 * 
 * This work has been performed in the framework of the SONATA project, funded by the European
 * Commission under Grant number 671517 through the Horizon 2020 and 5G-PPP programmes. The authors
 * would like to acknowledge the contributions of their colleagues of the SONATA partner consortium
 * (www.sonata-nfv.eu).
 *
 * @author Dario Valocchi (Ph.D.), UCL
 * 
 */

package sonata.kernel.WimAdaptor.wrapper;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.InputStreamReader;
import java.nio.charset.Charset;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.Properties;

import org.json.JSONObject;
import org.json.JSONTokener;
import org.slf4j.LoggerFactory;

public class WimRepo {


  private final static String configFilePath = "/etc/son-mano/postgres.config";
  private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(WimRepo.class);
  private Properties prop;

  /**
   * Create the a WimRepo that read from the config file, connect to the database, and if needed
   * creates the tables.
   * 
   */
  public WimRepo() {
    this.prop = this.parseConfigFile();

    Connection connection = null;
    Statement findDatabaseStmt = null;
    PreparedStatement findTablesStmt = null;
    Statement createDatabaseStmt = null;
    Statement stmt = null;
    ResultSet rs = null;
    String dbUrl = "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
        + prop.getProperty("repo_port") + "/" + "postgres";
    String user = prop.getProperty("user");
    String pass = prop.getProperty("pass");
    Logger.info("Connecting to postgresql at " + dbUrl);
    boolean errors = false;
    try {
      Class.forName("org.postgresql.Driver");
      connection = DriverManager.getConnection(dbUrl, user, pass);
      boolean isDatabaseSet = false;
      Logger.info("Connection opened successfully. Listing databases...");
      String sql;
      sql = "SELECT datname FROM pg_catalog.pg_database;";
      findDatabaseStmt = connection.createStatement();
      rs = findDatabaseStmt.executeQuery(sql);
      while (rs.next()) {
        String datname = rs.getString("datname");
        if (datname.equals("wimregistry") || datname.equals("WIMREGISTRY")) {
          isDatabaseSet = true;
        }
      }
      rs.close();

      if (!isDatabaseSet) {
        Logger.info("Database not set. Creating database...");
        sql = "CREATE DATABASE wimregistry;";
        stmt = connection.createStatement();
        stmt.execute(sql);
        sql = "GRANT ALL PRIVILEGES ON DATABASE wimregistry TO " + user + ";";
        createDatabaseStmt = connection.createStatement();

        Logger.info("Statement:" + createDatabaseStmt.toString());
        createDatabaseStmt.execute(sql);
      } else {
        Logger.info("Database already set.");
      }
      connection.close();

      // reconnect to the new database;

      dbUrl = "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
          + prop.getProperty("repo_port") + "/" + "wimregistry";
      Logger.info("Connecting to the new database: " + dbUrl);
      connection = DriverManager.getConnection(dbUrl, user, pass);


      boolean isEnvironmentSet = false;
      sql = "SELECT * FROM pg_catalog.pg_tables WHERE tableowner=?;";
      findTablesStmt = connection.prepareStatement(sql);
      findTablesStmt.setString(1, user);
      rs = findTablesStmt.executeQuery();
      while (rs.next()) {
        String tablename = rs.getString("tablename");
        if (tablename.equals("wim") || tablename.equals("WIM") || tablename.equals("attached_vim")
            || tablename.equals("attached_vim")) {
          isEnvironmentSet = true;
          break;
        }
      }
      if (stmt != null) {
        stmt.close();
      }
      if (!isEnvironmentSet) {
        stmt = connection.createStatement();
        sql = "CREATE TABLE wim " + "(UUID TEXT PRIMARY KEY NOT NULL," + " TYPE TEXT,"+" NAME TEXT,"
            + " VENDOR TEXT NOT NULL," + " ENDPOINT TEXT NOT NULL," + " USERNAME TEXT NOT NULL,"
            + " PASS TEXT," + " AUTHKEY TEXT);";
        stmt.executeUpdate(sql);
        sql = "CREATE TABLE attached_vim " + "(VIM_UUID TEXT PRIMARY KEY NOT NULL, "
            + "VIM_ADDRESS TEXT NOT NULL, "
            + "WIM_UUID TEXT NOT NULL REFERENCES wim(UUID));";
        stmt.executeUpdate(sql);

      }

    } catch (SQLException e) {
      Logger.error(e.getMessage(), e);
      errors = true;
    } catch (ClassNotFoundException e) {
      Logger.error(e.getMessage(), e);
      errors = true;
    } finally {
      try {
        if (stmt != null) {
          stmt.close();
        }
        if (connection != null) {
          connection.close();
        }
        if (rs != null) {
          rs.close();
        }
        if (connection != null) {
          connection.close();
        }
      } catch (SQLException e) {
        Logger.error(e.getMessage(), e);
      }
    }
    if (!errors) {
      Logger.info("Environment created successfully");
    } else {
      Logger.error("Errors creating the environment");
    }
    return;
  }

  /**
   * Write the wrapper record into the repository with the specified UUID.
   * 
   * @param uuid the UUID of the wrapper to store
   * @param record the WrapperRecord object with the information on the wrapper to store
   * 
   * @return true for process success
   */
  public boolean writeWimEntry(String uuid, WrapperRecord record) {
    boolean out = true;

    Connection connection = null;
    PreparedStatement stmt = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "wimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      String sql = "INSERT INTO WIM (UUID, TYPE, VENDOR, ENDPOINT, USERNAME, PASS, AUTHKEY, NAME) "
          + "VALUES (?, ?, ?, ?, ?, ?, ?, ?);";
      stmt = connection.prepareStatement(sql);
      stmt.setString(1, uuid);
      stmt.setString(2, record.getConfig().getWrapperType());
      stmt.setString(3, record.getConfig().getWimVendor().toString());
      stmt.setString(4, record.getConfig().getWimEndpoint().toString());
      stmt.setString(5, record.getConfig().getAuthUserName());
      stmt.setString(6, record.getConfig().getAuthPass());
      stmt.setString(7, record.getConfig().getAuthKey());
      stmt.setString(8, record.getConfig().getName());
      stmt.executeUpdate();
      connection.commit();
      stmt.close();
    } catch (SQLException e) {
      Logger.error(e.getMessage(), e);
      out = false;
    } catch (ClassNotFoundException e) {
      Logger.error(e.getMessage(), e);
      out = false;
    } finally {
      try {
        if (stmt != null) {
          stmt.close();
        }
        if (connection != null) {
          connection.close();
        }
      } catch (SQLException e) {
        Logger.error(e.getMessage(), e);
        out = false;
      }
    }
    Logger.info("Records created successfully");

    return out;
  }

  /**
   * Remove the wrapper identified by the specified UUID from the repository.
   * 
   * @param uuid the UUID of the wrapper to remove
   * 
   * @return true for process success
   */
  public boolean removeWimEntry(String uuid) {
    boolean out = true;
    Connection connection = null;
    PreparedStatement stmt = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "wimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);
      String sql = "DELETE from WIM where UUID=?;";
      stmt = connection.prepareStatement(sql);
      stmt.setString(1, uuid);
      stmt.executeUpdate();
      connection.commit();
    } catch (SQLException e) {
      Logger.error(e.getMessage(), e);
      out = false;
    } catch (ClassNotFoundException e) {
      Logger.error(e.getMessage(), e);
      out = false;
    } finally {
      try {
        if (stmt != null) {
          stmt.close();
        }
        if (connection != null) {
          connection.close();
        }
      } catch (SQLException e) {
        Logger.error(e.getMessage(), e);
        out = false;

      }
    }
    Logger.info("Operation done successfully");
    return out;

  }

  /**
   * update the wrapper record into the repository with the specified UUID.
   * 
   * @param uuid the UUID of the wrapper to update
   * @param record the WrapperRecord object with the information on the wrapper to store
   * 
   * @return true for process success
   */
  public boolean updateWimEntry(String uuid, WrapperRecord record) {
    boolean out = true;

    Connection connection = null;
    PreparedStatement stmt = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "wimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);


      String sql = "UPDATE WIM set (TYPE, VENDOR, ENDPOINT, USERNAME, PASS, AUTHKEY, NAME) "
          + "VALUES (?,?,?,?,?,?,?) WHERE UUID=?;";

      stmt = connection.prepareStatement(sql);
      stmt.setString(1, record.getConfig().getWrapperType());
      stmt.setString(2, record.getConfig().getWimVendor().toString());
      stmt.setString(3, record.getConfig().getWimEndpoint().toString());
      stmt.setString(4, record.getConfig().getAuthUserName());
      stmt.setString(5, record.getConfig().getAuthPass());
      stmt.setString(6, record.getConfig().getAuthKey());
      stmt.setString(7, record.getConfig().getName());
      stmt.setString(8, uuid);


      stmt.executeUpdate(sql);
      connection.commit();
    } catch (SQLException e) {
      Logger.error(e.getMessage(), e);
      out = false;
    } catch (ClassNotFoundException e) {
      Logger.error(e.getMessage(), e);
      out = false;
    } finally {
      try {
        if (stmt != null) {
          stmt.close();
        }
        if (connection != null) {
          connection.close();
        }
      } catch (SQLException e) {
        Logger.error(e.getMessage(), e);
        out = false;

      }
    }
    Logger.info("Records created successfully");

    return out;
  }

  /**
   * Retrieve the wrapper record with the specified UUID from the repository.
   * 
   * @param uuid the UUID of the wrapper to retrieve
   * 
   * @return the WrapperRecord representing the wrapper, null if the wrapper is not registere in the
   *         repository
   */
  public WrapperRecord readWimEntry(String uuid) {

    WrapperRecord output = null;

    Connection connection = null;
    PreparedStatement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "wimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection.prepareStatement("SELECT * FROM WIM WHERE UUID=?;");
      stmt.setString(1, uuid);
      rs = stmt.executeQuery();

      if (rs.next()) {
        String wrapperType = rs.getString("TYPE");
        String vendor = rs.getString("VENDOR");
        String urlString = rs.getString("ENDPOINT");
        String user = rs.getString("USERNAME");
        String pass = rs.getString("PASS");
        String key = rs.getString("AUTHKEY");
        String name = rs.getString("NAME");

        WrapperConfiguration config = new WrapperConfiguration();
        config.setUuid(uuid);
        config.setWrapperType(wrapperType);
        config.setWimVendor(WimVendor.getByName(vendor));
        config.setWimEndpoint(urlString);
        config.setAuthUserName(user);
        config.setAuthPass(pass);
        config.setAuthKey(key);
        config.setName(name);

        Wrapper wrapper = WrapperFactory.createWrapper(config);
        output = new WrapperRecord(wrapper, config);


      } else {
        output = null;
      }
    } catch (SQLException e) {
      Logger.error(e.getMessage(), e);
      output = null;
    } catch (ClassNotFoundException e) {
      Logger.error(e.getMessage(), e);
      output = null;
    } finally {
      try {
        if (stmt != null) {
          stmt.close();
        }
        if (rs != null) {
          rs.close();
        }
        if (connection != null) {
          connection.close();
        }
      } catch (SQLException e) {
        Logger.error(e.getMessage(), e);
        output = null;

      }
    }
    Logger.info("Operation done successfully");
    return output;

  }

  /**
   * Retrieve the WIM record managing connectivity in for the serviced given net segment.
   * 
   * @param uuid the UUID of the wrapper to retrieve
   * 
   * @return the WrapperRecord representing the wrapper, null if the wrapper is not registered in
   *         the repository
   */
  public WrapperRecord readWimEntryFromVimUuid(String vimUuid) {

    WrapperRecord output = null;

    Connection connection = null;
    PreparedStatement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "wimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection.prepareStatement(
          "SELECT * FROM wim,attached_vim WHERE wim.uuid = attached_vim.wim_uuid AND attached_vim.vim_uuid=?;");
      stmt.setString(1, vimUuid);
      rs = stmt.executeQuery();

      if (rs.next()) {
        String uuid = rs.getString("UUID");
        String wrapperType = rs.getString("TYPE");
        String vendor = rs.getString("VENDOR");
        String urlString = rs.getString("ENDPOINT");
        String user = rs.getString("USERNAME");
        String pass = rs.getString("PASS");
        String key = rs.getString("AUTHKEY");
        String name = rs.getString("NAME");

        WrapperConfiguration config = new WrapperConfiguration();
        config.setUuid(uuid);
        config.setWrapperType(wrapperType);
        config.setWimVendor(WimVendor.getByName(vendor));
        config.setWimEndpoint(urlString);
        config.setAuthUserName(user);
        config.setAuthPass(pass);
        config.setAuthKey(key);
        config.setName(name);

        Wrapper wrapper = WrapperFactory.createWrapper(config);
        output = new WrapperRecord(wrapper, config);


      } else {
        output = null;
      }
    } catch (SQLException e) {
      Logger.error(e.getMessage(), e);
      output = null;
    } catch (ClassNotFoundException e) {
      Logger.error(e.getMessage(), e);
      output = null;
    } finally {
      try {
        if (stmt != null) {
          stmt.close();
        }
        if (rs != null) {
          rs.close();
        }
        if (connection != null) {
          connection.close();
        }
      } catch (SQLException e) {
        Logger.error(e.getMessage(), e);
        output = null;

      }
    }
    Logger.info("Operation done successfully");
    return output;

  }

  /**
   * List the compute WIMs stored in the repository.
   * 
   * @return an arraylist of String with the UUID of the registered WIMs, null if error occurs
   */
  public ArrayList<String> listWims() {
    ArrayList<String> out = new ArrayList<String>();

    Connection connection = null;
    Statement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "wimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection.createStatement();
      rs = stmt.executeQuery("SELECT * FROM WIM;");
      while (rs.next()) {
        String uuid = rs.getString("UUID");
        out.add(uuid);
      }

    } catch (SQLException e) {
      Logger.error(e.getMessage(), e);
      out = null;
    } catch (ClassNotFoundException e) {
      Logger.error(e.getMessage(), e);
      out = null;
    } finally {
      try {
        if (stmt != null) {
          stmt.close();
        }
        if (rs != null) {
          rs.close();
        }
        if (connection != null) {
          connection.close();
        }
      } catch (SQLException e) {
        Logger.error(e.getMessage(), e);

      }
    }
    Logger.info("Operation done successfully");
    return out;
  }



  private Properties parseConfigFile() {
    Properties prop = new Properties();
    try {
      InputStreamReader in =
          new InputStreamReader(new FileInputStream(configFilePath), Charset.forName("UTF-8"));

      JSONTokener tokener = new JSONTokener(in);

      JSONObject jsonObject = (JSONObject) tokener.nextValue();

      String repoUrl = jsonObject.getString("repo_host");
      String repoPort = jsonObject.getString("repo_port");
      String user = jsonObject.getString("user");
      String pass = jsonObject.getString("pass");
      prop.put("repo_host", repoUrl);
      prop.put("repo_port", repoPort);
      prop.put("user", user);
      prop.put("pass", pass);
    } catch (FileNotFoundException e) {
      Logger.error(e.getMessage(), e);
    }

    return prop;
  }

  public boolean attachVim(String wimUuid, String vimUuid, String vimAddress) {
    boolean out = true;

    Connection connection = null;
    PreparedStatement stmt = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "wimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      String sql = "INSERT INTO attached_vim (VIM_UUID, VIM_ADDRESS, WIM_UUID) "
          + "VALUES (?, ?, ?);";
      stmt = connection.prepareStatement(sql);
      stmt.setString(1, vimUuid);
      stmt.setString(2, vimAddress);
      stmt.setString(3, wimUuid);
      stmt.executeUpdate();
      connection.commit();
      stmt.close();
    } catch (SQLException e) {
      Logger.error(e.getMessage(), e);
      out = false;
    } catch (ClassNotFoundException e) {
      Logger.error(e.getMessage(), e);
      out = false;
    } finally {
      try {
        if (stmt != null) {
          stmt.close();
        }
        if (connection != null) {
          connection.close();
        }
      } catch (SQLException e) {
        Logger.error(e.getMessage(), e);
        out = false;
      }
    }
    Logger.info("Records created successfully");

    return out;
  }

  public ArrayList<String> readAttachedVim(String wimUuid) {
    ArrayList<String> output = new ArrayList<String>();
    Connection connection = null;
    PreparedStatement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "wimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection.prepareStatement(
          "SELECT * FROM attached_vim WHERE wim_uuid = ?;");
      stmt.setString(1, wimUuid);
      rs = stmt.executeQuery();

      while (rs.next()) {
        String vimUuid = rs.getString("VIM_UUID");
        output.add(vimUuid);

      }
      
    } catch (SQLException e) {
      Logger.error(e.getMessage(), e);
      output = null;
    } catch (ClassNotFoundException e) {
      Logger.error(e.getMessage(), e);
      output = null;
    } finally {
      try {
        if (stmt != null) {
          stmt.close();
        }
        if (rs != null) {
          rs.close();
        }
        if (connection != null) {
          connection.close();
        }
      } catch (SQLException e) {
        Logger.error(e.getMessage(), e);
        output = null;

      }
    }
    Logger.info("Operation done successfully");
    return output;

  }

  public String readVimAddressFromVimUuid(String vimUuid) {
    String output = null;
    Connection connection = null;
    PreparedStatement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "wimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection.prepareStatement(
          "SELECT vim_address FROM attached_vim WHERE vim_uuid = ?;");
      stmt.setString(1, vimUuid);
      rs = stmt.executeQuery();

      while (rs.next()) {
        output = rs.getString("vim_address");
         

      }
      
    } catch (SQLException e) {
      Logger.error(e.getMessage(), e);
      output = null;
    } catch (ClassNotFoundException e) {
      Logger.error(e.getMessage(), e);
      output = null;
    } finally {
      try {
        if (stmt != null) {
          stmt.close();
        }
        if (rs != null) {
          rs.close();
        }
        if (connection != null) {
          connection.close();
        }
      } catch (SQLException e) {
        Logger.error(e.getMessage(), e);
        output = null;

      }
    }
    Logger.info("Operation done successfully");
    return output;

  }
}
