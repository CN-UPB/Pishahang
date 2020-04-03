/*
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

package sonata.kernel.vimadaptor.wrapper;

import org.json.JSONObject;
import org.json.JSONTokener;
import org.slf4j.LoggerFactory;

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

public class VimRepo {


  private static final String configFilePath = "/etc/son-mano/postgres.config";
  private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(VimRepo.class);
  private Properties prop;

  /**
   * Create the a VimRepo that read from the config file, connect to the database, and if needed
   * creates the tables.
   * 
   */
  public VimRepo() {
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
        if (datname.equals("vimregistry") || datname.equals("VIMREGISTRY")) {
          isDatabaseSet = true;
        }
      }
      rs.close();

      if (!isDatabaseSet) {
        Logger.info("Database not set. Creating database...");
        sql = "CREATE DATABASE vimregistry;";
        stmt = connection.createStatement();
        stmt.execute(sql);
        sql = "GRANT ALL PRIVILEGES ON DATABASE vimregistry TO " + user + ";";
        createDatabaseStmt = connection.createStatement();

        Logger.info("Statement:" + createDatabaseStmt.toString());
        createDatabaseStmt.execute(sql);
      } else {
        Logger.info("Database already set.");
      }
      connection.close();

      // reconnect to the new database;

      dbUrl = "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
          + prop.getProperty("repo_port") + "/" + "vimregistry";
      Logger.info("Connecting to the new database: " + dbUrl);
      connection = DriverManager.getConnection(dbUrl, user, pass);


      boolean isEnvironmentSet = false;
      sql = "SELECT * FROM pg_catalog.pg_tables WHERE tableowner=?;";
      findTablesStmt = connection.prepareStatement(sql);
      findTablesStmt.setString(1, user);
      rs = findTablesStmt.executeQuery();
      while (rs.next()) {
        String tablename = rs.getString("tablename");
        if (tablename.toLowerCase().equals("vim")
            || tablename.toLowerCase().equals("service_instances")
            || tablename.toLowerCase().equals("function_instances")
            || tablename.toLowerCase().equals("link_vim")
            || tablename.toLowerCase().equals("cloud_service_instances")) {
          isEnvironmentSet = true;
          break;
        }
      }
      if (stmt != null) {
        stmt.close();
      }
      if (!isEnvironmentSet) {
        stmt = connection.createStatement();
        sql = "CREATE TABLE vim " + "(UUID TEXT PRIMARY KEY NOT NULL," + "NAME TEXT,"
            + " TYPE TEXT NOT NULL," + " VENDOR TEXT NOT NULL," + " ENDPOINT TEXT NOT NULL,"
            + " USERNAME TEXT NOT NULL," + " DOMAIN TEXT NOT NULL," + " CONFIGURATION TEXT NOT NULL," + " CITY TEXT,"
            + "COUNTRY TEXT," + " PASS TEXT," + " AUTHKEY TEXT" + ");";
        stmt.executeUpdate(sql);
        sql = "CREATE TABLE service_instances " + "(" + "INSTANCE_UUID TEXT NOT NULL,"
            + " VIM_INSTANCE_UUID TEXT NOT NULL," + " VIM_INSTANCE_NAME TEXT NOT NULL,"
            + " VIM_UUID TEXT NOT NULL," + " PRIMARY KEY (INSTANCE_UUID, VIM_UUID)" + ");";
        stmt.executeUpdate(sql);
        sql = "CREATE TABLE function_instances " + "(" + "INSTANCE_UUID TEXT PRIMARY KEY NOT NULL,"
            + " SERVICE_INSTANCE_UUID TEXT NOT NULL," + " VIM_UUID TEXT NOT NULL,"
            + " FOREIGN KEY (SERVICE_INSTANCE_UUID, VIM_UUID) REFERENCES service_instances(INSTANCE_UUID, VIM_UUID) ON DELETE CASCADE"
            + ");";
        stmt.executeUpdate(sql);
        sql = "CREATE TABLE link_vim "
            + "(COMPUTE_UUID TEXT NOT NULL REFERENCES vim(UUID) ON DELETE CASCADE,"
            + " NETWORKING_UUID TEXT NOT NULL REFERENCES vim(UUID) ON DELETE CASCADE" + ");";
        stmt.executeUpdate(sql);
        sql = "CREATE TABLE cloud_service_instances " + "(" + "INSTANCE_UUID TEXT PRIMARY KEY NOT NULL,"
            + " SERVICE_INSTANCE_UUID TEXT NOT NULL," + " VIM_UUID TEXT NOT NULL,"
            + " FOREIGN KEY (SERVICE_INSTANCE_UUID, VIM_UUID) REFERENCES service_instances(INSTANCE_UUID, VIM_UUID) ON DELETE CASCADE"
            + ");";
        stmt.executeUpdate(sql);
      }

    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
      }
    }
    if (!errors) {
      Logger.info("Environment created successfully");
    } else {
      Logger.info("Errors creating the environment");
    }
    return;
  }


  /**
   * List the compute VIMs stored in the repository.
   * 
   * @return an arraylist of String with the UUID of the registered VIMs, null if error occurs
   */
  public ArrayList<String> getComputeVims() {
    ArrayList<String> out = new ArrayList<String>();

    Connection connection = null;
    Statement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection.createStatement();
      rs = stmt.executeQuery("SELECT * FROM VIM WHERE TYPE='compute';");
      while (rs.next()) {
        String uuid = rs.getString("UUID");
        out.add(uuid);
      }

    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());

      }
    }
    return out;
  }

  /**
   * Get the VIM UUID where the given VNF is deployed.
   * 
   * @param functionId the instance UUID of the VNF
   * 
   * @return the uuid of the VIM
   * 
   */
  public String getComputeVimUuidByFunctionInstanceId(String functionId) {
    String output = null;

    Connection connection = null;
    PreparedStatement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection
          .prepareStatement("SELECT VIM_UUID FROM function_instances  WHERE INSTANCE_UUID=?;");
      stmt.setString(1, functionId);
      rs = stmt.executeQuery();

      if (rs.next()) {

        output = rs.getString("VIM_UUID");

      } else {
        output = null;
      }
    } catch (SQLException e) {
      Logger.error(e.getMessage());
      output = null;
    } catch (ClassNotFoundException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        output = null;

      }
    }
    return output;
  }

  /**
   * Return a list of the compute VIMs hosting at least one VNFs of the given Service Instance.
   * 
   * @param instanceUuid the UUID that identifies the Service Instance
   * @return an array of String objecst representing the UUID of the VIMs
   */
  public String[] getComputeVimUuidFromInstance(String instanceUuid) {

    String[] output = null;

    Connection connection = null;
    PreparedStatement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection
          .prepareStatement("SELECT VIM_UUID FROM service_instances  WHERE INSTANCE_UUID=?;");
      stmt.setString(1, instanceUuid);
      rs = stmt.executeQuery();
      ArrayList<String> uuids = new ArrayList<String>();

      while (rs.next()) {
        uuids.add(rs.getString("VIM_UUID"));
      }
      output = new String[uuids.size()];
      output = uuids.toArray(output);

    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        output = null;

      }
    }

    return output;

  }

  /**
   * Get the NetworkWrapper identified by the given UUID.
   * 
   * @param computeUuid the uuid of the network VIM
   * @return
   */
  public NetworkWrapper getNetworkVim(String vimUuid) {
    NetworkWrapper output = null;
    Connection connection = null;
    PreparedStatement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt =
          connection.prepareStatement("SELECT * FROM vim WHERE vim.UUID=? AND vim.TYPE='network';");
      stmt.setString(1, vimUuid);
      rs = stmt.executeQuery();

      if (rs.next()) {
        String uuid = rs.getString("UUID");
        WrapperType wrapperType = WrapperType.getByName(rs.getString("TYPE"));
        String vendorString = rs.getString("VENDOR");
        VimVendor vendor = null;
        if (wrapperType.equals(WrapperType.COMPUTE)) {
          vendor = ComputeVimVendor.getByName(vendorString);
        } else if (wrapperType.equals(WrapperType.NETWORK)) {
          vendor = NetworkVimVendor.getByName(vendorString);
        }
        String urlString = rs.getString("ENDPOINT");
        String user = rs.getString("USERNAME");
        String pass = rs.getString("PASS");
        String domain = rs.getString("DOMAIN");
        String key = rs.getString("AUTHKEY");
        String configuration = rs.getString("CONFIGURATION");
        String city = rs.getString("CITY");
        String country = rs.getString("COUNTRY");

        WrapperConfiguration config = new WrapperConfiguration();
        config.setUuid(uuid);
        config.setWrapperType(wrapperType);
        config.setVimVendor(vendor);
        config.setVimEndpoint(urlString);
        config.setConfiguration(configuration);
        config.setAuthUserName(user);
        config.setAuthPass(pass);
        config.setDomain(domain);
        config.setAuthKey(key);
        config.setCity(city);
        config.setCountry(country);

        output = (NetworkWrapper) WrapperFactory.createWrapper(config);


      } else {
        output = null;
      }
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        output = null;

      }
    }
    return output;

  }

  /**
   * Get the NetworkWrapper associated to the given computeVim.
   * 
   * @param computeUuid the uuid of the computeVim
   * @return
   */
  public String getNetworkVimFromComputeVimUuid(String computeUuid) {
    String output = null;
    Connection connection = null;
    PreparedStatement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection.prepareStatement(
          "SELECT vim.UUID FROM vim,link_vim WHERE vim.UUID=LINK_VIM.NETWORKING_UUID AND LINK_VIM.COMPUTE_UUID=?;");
      stmt.setString(1, computeUuid);
      rs = stmt.executeQuery();

      if (rs.next()) {
        String uuid = rs.getString("UUID");

        // WrapperType wrapperType = WrapperType.getByName(rs.getString("TYPE"));
        // String vendor = rs.getString("VENDOR");
        // String urlString = rs.getString("ENDPOINT");
        // String user = rs.getString("USERNAME");
        // String pass = rs.getString("PASS");
        // String key = rs.getString("AUTHKEY");
        // String configuration = rs.getString("CONFIGURATION");
        // String city = rs.getString("CITY");
        // String country = rs.getString("COUNTRY");
        //
        // WrapperConfiguration config = new WrapperConfiguration();
        // config.setUuid(uuid);
        // config.setWrapperType(wrapperType);
        // config.setVimVendor(NetworkVimVendor.getByName(vendor));
        // config.setVimEndpoint(urlString);
        // config.setConfiguration(configuration);
        // config.setCity(city);
        // config.setCountry(country);
        // config.setAuthUserName(user);
        // config.setAuthPass(pass);
        // config.setAuthKey(key);
        //
        // Wrapper wrapper = WrapperFactory.createWrapper(config);
        // output = new WrapperRecord(wrapper, config, null);

        output = uuid;

      } else {
        output = null;
      }
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        output = null;

      }
    }
    return output;

  }

  /**
   * @return
   */
  public ArrayList<String> getNetworkVims() {
    ArrayList<String> out = new ArrayList<String>();

    Connection connection = null;
    Statement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection.createStatement();
      rs = stmt.executeQuery("SELECT * FROM VIM WHERE TYPE='network';");
      while (rs.next()) {
        String uuid = rs.getString("UUID");
        out.add(uuid);
      }

    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());

      }
    }
    return out;
  }

  /**
   * Get the UUID used by the VIM to identify the given service instance.
   * 
   * @param instanceUuid the instance UUID of the service to remove
   * 
   * @return the logical name used by the VIM to identify the service instance
   * 
   */
  public String getServiceInstanceVimName(String instanceUuid) {

    String output = null;

    Connection connection = null;
    PreparedStatement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection.prepareStatement(
          "SELECT VIM_INSTANCE_NAME FROM service_instances  WHERE INSTANCE_UUID=?;");
      stmt.setString(1, instanceUuid);
      rs = stmt.executeQuery();

      if (rs.next()) {

        output = rs.getString("VIM_INSTANCE_NAME");

      } else {
        output = null;
      }
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        output = null;

      }
    }

    return output;

  }

  /**
   * Get the UUID used by the given VIM to identify the given service instance.
   * 
   * @param instanceUuid the instance UUID of the service to remove
   * @param vimUuid the UUID of the VIM
   * 
   * @return the logical name used by the VIM to identify the service instance
   * 
   */
  public String getServiceInstanceVimName(String instanceUuid, String vimUuid) {

    String output = null;

    Connection connection = null;
    PreparedStatement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection.prepareStatement(
          "SELECT VIM_INSTANCE_NAME FROM service_instances  WHERE INSTANCE_UUID=? AND VIM_UUID=?;");
      stmt.setString(1, instanceUuid);
      stmt.setString(2, vimUuid);
      rs = stmt.executeQuery();

      if (rs.next()) {

        output = rs.getString("VIM_INSTANCE_NAME");

      } else {
        output = null;
      }
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        output = null;

      }
    }

    return output;

  }

  /**
   * Get the name used to reference the service in the in the scope of the VIM where given VNF is
   * deployed.
   * 
   * @param functionId the instance UUID of the VNF
   * 
   * @return the mnemonic name used in the VIM scope to reference the service
   * 
   */
  public String getServiceInstanceVimNameByFunction(String functionId) {
    String output = null;
    Connection connection = null;
    PreparedStatement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection.prepareStatement(
          "SELECT VIM_INSTANCE_NAME FROM service_instances AS s,function_instances AS f WHERE s.INSTANCE_UUID=f.SERVICE_INSTANCE_UUID AND f.INSTANCE_UUID=?;");
      stmt.setString(1, functionId);
      rs = stmt.executeQuery();
      if (rs.next()) {

        output = rs.getString("VIM_INSTANCE_NAME");

      } else {
        output = null;
      }
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        output = null;

      }
    }
    return output;
  }

  /**
   * Get the UUID used by the VIM to identify the given service instance.
   * 
   * @param instanceUuid the instance UUID of the service to retrieve
   * 
   * @return the uuid used by the VIM to identify the service instance
   * 
   */
  public String getServiceInstanceVimUuid(String instanceUuid) {

    String output = null;

    Connection connection = null;
    PreparedStatement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection.prepareStatement(
          "SELECT VIM_INSTANCE_UUID FROM service_instances  WHERE INSTANCE_UUID=?;");
      stmt.setString(1, instanceUuid);
      rs = stmt.executeQuery();

      if (rs.next()) {

        output = rs.getString("VIM_INSTANCE_UUID");

      } else {
        output = null;
      }
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        output = null;

      }
    }
    return output;
  }

  /**
   * @param instanceId
   * @param vimUuid
   * @return
   */
  public String getServiceInstanceVimUuid(String instanceId, String vimUuid) {
    String output = null;

    Connection connection = null;
    PreparedStatement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection.prepareStatement(
          "SELECT VIM_INSTANCE_UUID FROM service_instances  WHERE INSTANCE_UUID=? AND VIM_UUID=?;");
      stmt.setString(1, instanceId);
      stmt.setString(2, vimUuid);
      rs = stmt.executeQuery();

      if (rs.next()) {

        output = rs.getString("VIM_INSTANCE_UUID");

      } else {
        output = null;
      }
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        output = null;

      }
    }
    return output;
  }

  /**
   * Get the UUID used to reference the service in the scope of the VIM where given VNF is deployed.
   * 
   * @param functionId the instance UUID of the VNF
   * 
   * @return the uuid used in the VIM scope to reference the service
   * 
   */
  public String getServiceInstanceVimUuidByFunction(String functionId) {
    String output = null;
    Connection connection = null;
    PreparedStatement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection.prepareStatement(
          "SELECT VIM_INSTANCE_UUID FROM service_instances AS s,function_instances AS f WHERE s.INSTANCE_UUID=f.SERVICE_INSTANCE_UUID AND s.VIM_UUID=f.VIM_UUID AND f.INSTANCE_UUID=?;");
      stmt.setString(1, functionId);
      rs = stmt.executeQuery();
      if (rs.next()) {

        output = rs.getString("VIM_INSTANCE_UUID");

      } else {
        output = null;
      }
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        output = null;

      }
    }
    return output;
  }

  /**
   * Retrieve the wrapper record with the specified UUID from the repository.
   * 
   * @param uuid the UUID of the wrapper to retrieve
   * 
   * @return the WrapperRecord representing the wrapper, null if the wrapper is not registere in the
   *         repository
   */
  public Wrapper readVimEntry(String uuid) {

    Wrapper output = null;

    Connection connection = null;
    PreparedStatement stmt = null;
    ResultSet rs = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      stmt = connection.prepareStatement("SELECT * FROM VIM WHERE UUID=?;");
      stmt.setString(1, uuid);
      rs = stmt.executeQuery();

      if (rs.next()) {
        String stringWrapperType = rs.getString("TYPE");
        WrapperType wrapperType = WrapperType.getByName(stringWrapperType);
        String vendorString = rs.getString("VENDOR");
        String urlString = rs.getString("ENDPOINT");
        String user = rs.getString("USERNAME");
        String pass = rs.getString("PASS");
        String domain = rs.getString("DOMAIN");       
        String configuration = rs.getString("CONFIGURATION");
        String city = rs.getString("CITY");
        String country = rs.getString("COUNTRY");
        String key = rs.getString("AUTHKEY");
        String name = rs.getString("NAME");

        WrapperConfiguration config = new WrapperConfiguration();
        config.setUuid(uuid);
        config.setWrapperType(wrapperType);
        config.setConfiguration(configuration);
        config.setCity(city);
        config.setCountry(country);
        config.setVimEndpoint(urlString);
        config.setAuthUserName(user);
        config.setAuthPass(pass);
        config.setDomain(domain);
        config.setAuthKey(key);
        config.setName(name);

        if (wrapperType.equals(WrapperType.COMPUTE)) {
          VimVendor vendor = ComputeVimVendor.getByName(vendorString);
          config.setVimVendor(vendor);
        } else if (wrapperType.equals(WrapperType.NETWORK)) {
          VimVendor vendor = NetworkVimVendor.getByName(vendorString);
          config.setVimVendor(vendor);
        }
        output = WrapperFactory.createWrapper(config);

      } else {
        output = null;
      }
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        output = null;

      }
    }
    return output;

  }

  /**
   * @param uuid
   */
  public boolean removeNetworkVimLink(String networkingUuid) {
    boolean out = true;

    Connection connection = null;
    PreparedStatement stmt = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      String sql = "DELETE FROM LINK_VIM WHERE NETWORKING_UUID=?;";
      stmt = connection.prepareStatement(sql);
      stmt.setString(1, networkingUuid);
      stmt.executeUpdate();
      connection.commit();
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        out = false;
      }
    }
    if (!out) {
      Logger.info("Network VIM link removed successfully");
    }

    return out;
  }

  /**
   * delete the service instance record into the repository.
   * 
   * @param instanceUuid the uuid of the instance in the NSD
   * 
   * @return true for process success
   */
  public boolean removeServiceInstanceEntry(String instanceUuid, String vimUuid) {
    boolean out = true;

    Connection connection = null;
    PreparedStatement stmt = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      String sql = "DELETE FROM service_instances WHERE INSTANCE_UUID=? AND VIM_UUID=?;";
      stmt = connection.prepareStatement(sql);
      stmt.setString(1, instanceUuid);
      stmt.setString(2, vimUuid);
      stmt.executeUpdate();
      connection.commit();
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        out = false;
      }
    }
    if (!out) {
      Logger.info("Service instance removed successfully");
    }

    return out;
  }

  /**
   * Remove the wrapper identified by the specified UUID from the repository.
   * 
   * @param uuid the UUID of the wrapper to remove
   * 
   * @return true for process success
   */
  public boolean removeVimEntry(String uuid) {
    boolean out = true;
    Connection connection = null;
    PreparedStatement stmt = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      String sql = "DELETE from VIM where UUID=?;";
      stmt = connection.prepareStatement(sql);
      stmt.setString(1, uuid);
      stmt.executeUpdate();
      connection.commit();
    } catch (SQLException e) {
      Logger.error(e.getMessage());
      out = false;
    } catch (ClassNotFoundException e) {
      Logger.error(e.getMessage(), e);;
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
        Logger.error(e.getMessage());
        out = false;

      }
    }
    Logger.info("VIM removed successfully");
    return out;
  }

  /**
   * Update the instance record into the repository.
   * 
   * @param instanceUuid the uuid of the instance in the NSD
   * @param vimInstanceUuid the uuid used by the VIM to identify the stack
   * @param vimInstanceName the name used by the VIM to identify the stack
   * @param vimUuid the UUID of the compute VIM where the service is deployed
   * 
   * @return true for process success
   */
  public boolean updateServiceInstanceEntry(String instanceUuid, String vimInstanceUuid,
      String vimInstanceName, String vimUuid) {
    boolean out = true;

    Connection connection = null;
    PreparedStatement stmt = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      String sql = "UPDATE service_instances  set (VIM_INSTANCE_UUID, VIM_INSTANCE_NAME, VIM_UUID) "
          + "VALUES (?, ?, ?) WHERE INSTANCE_UUID=?;";
      stmt = connection.prepareStatement(sql);
      stmt.setString(1, vimInstanceUuid);
      stmt.setString(2, vimInstanceName);
      stmt.setString(3, vimUuid);
      stmt.setString(4, instanceUuid);
      stmt.executeUpdate();
      connection.commit();
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        out = false;
      }
    }
    if (!out) {
      Logger.info("Service instance updated successfully");
    }

    return out;
  }

  /**
   * update the wrapper record into the repository with the specified UUID.
   * 
   * @param uuid the UUID of the wrapper to update
   * @param wrapper the Wrapper object with the information on the wrapper to store
   * 
   * @return true for process success
   */
  public boolean updateVimEntry(String uuid, Wrapper wrapper) {
    boolean out = true;

    Connection connection = null;
    PreparedStatement stmt = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);


      String sql = "UPDATE VIM set "
          + "(NAME, TYPE, VENDOR, ENDPOINT, USERNAME, CONFIGURATION, CITY, COUNTRY, PASS, AUTHKEY, DOMAIN) "
          + "VALUES (?,?,?,?,?,?,?,?,?,?,?) WHERE UUID=?;";

      stmt = connection.prepareStatement(sql);
      stmt.setString(1, wrapper.getConfig().getWrapperType().toString());
      stmt.setString(2, wrapper.getConfig().getName());
      stmt.setString(3, wrapper.getConfig().getVimVendor().toString());
      stmt.setString(4, wrapper.getConfig().getVimEndpoint().toString());
      stmt.setString(5, wrapper.getConfig().getAuthUserName());
      stmt.setString(6, wrapper.getConfig().getConfiguration());
      stmt.setString(7, wrapper.getConfig().getCity());
      stmt.setString(8, wrapper.getConfig().getCountry());
      stmt.setString(9, wrapper.getConfig().getAuthPass());
      stmt.setString(10, wrapper.getConfig().getAuthKey());
      stmt.setString(11, wrapper.getConfig().getDomain());
      stmt.setString(12, uuid);


      stmt.executeUpdate(sql);
      connection.commit();
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        out = false;

      }
    }
    Logger.info("Records created successfully");

    return out;
  }

  /**
   * write the function instance record into the repository.
   * 
   * @param functionInstanceUuid the uuid of the function instance
   * @param serviceInstanceUuid the uuid of the service instance this function instance is part of.
   * @param computeWrapperUuid the uuid of the NFVi-PoP this function is deployed in.
   * 
   * @return true for process success
   */
  public boolean writeFunctionInstanceEntry(String functionInstanceUuid, String serviceInstanceUuid,
      String computeWrapperUuid) {
    boolean out = true;

    Connection connection = null;
    PreparedStatement stmt = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      String sql =
          "INSERT INTO function_instances  (INSTANCE_UUID, SERVICE_INSTANCE_UUID, VIM_UUID) "
              + "VALUES (?, ?, ?);";
      stmt = connection.prepareStatement(sql);
      stmt.setString(1, functionInstanceUuid);
      stmt.setString(2, serviceInstanceUuid);
      stmt.setString(3, computeWrapperUuid);
      stmt.executeUpdate();
      connection.commit();
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        out = false;
      }
    }
    if (!out) {
      Logger.info("Function Instance written successfully");
    }

    return out;
  }

  /**
   * write the cloud service instance record into the repository.
   *
   * @param cloudServiceInstanceUuid the uuid of the cloud service instance
   * @param serviceInstanceUuid the uuid of the service instance this cloud service instance is part of.
   * @param computeWrapperUuid the uuid of the NFVi-PoP this cloud service is deployed in.
   *
   * @return true for process success
   */
  public boolean writeCloudServiceInstanceEntry(String cloudServiceInstanceUuid, String serviceInstanceUuid,
                                            String computeWrapperUuid) {
    boolean out = true;

    Connection connection = null;
    PreparedStatement stmt = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
              DriverManager.getConnection(
                      "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                              + prop.getProperty("repo_port") + "/" + "vimregistry",
                      prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      String sql =
              "INSERT INTO cloud_service_instances  (INSTANCE_UUID, SERVICE_INSTANCE_UUID, VIM_UUID) "
                      + "VALUES (?, ?, ?);";
      stmt = connection.prepareStatement(sql);
      stmt.setString(1, cloudServiceInstanceUuid);
      stmt.setString(2, serviceInstanceUuid);
      stmt.setString(3, computeWrapperUuid);
      stmt.executeUpdate();
      connection.commit();
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        out = false;
      }
    }
    if (out) {
      Logger.info("Cloud Service Instance written successfully");
    }

    return out;
  }

  /**
   * Write the association between NetworkWrapper and ComputeWrapper.
   * 
   * @param computeUuid the uuid of the compute wrapper
   * @param networkingUuid the uuid of the networking wrapper
   * @return true for success
   */
  public boolean writeNetworkVimLink(String computeUuid, String networkingUuid) {
    boolean out = true;

    Connection connection = null;
    PreparedStatement stmt = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      String sql = "INSERT INTO LINK_VIM (COMPUTE_UUID, NETWORKING_UUID) " + "VALUES (?, ?);";
      stmt = connection.prepareStatement(sql);
      stmt.setString(1, computeUuid);
      stmt.setString(2, networkingUuid);
      stmt.executeUpdate();
      connection.commit();
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        out = false;
      }
    }
    if (out) {
      Logger.info("Network vim link written successfully");
    }

    return out;
  }


  /**
   * Write the instance record into the repository.
   * 
   * @param instanceUuid the uuid of the instance in the NSD
   * @param vimInstanceUuid the uuid used by the VIM to identify the stack
   * @param vimInstanceName the name used by the VIM to identify the stack
   * @param vimUuid the uuid of the compute VIM where the instance is deployed
   * 
   * @return true for process success
   */
  public boolean writeServiceInstanceEntry(String instanceUuid, String vimInstanceUuid,
      String vimInstanceName, String vimUuid) {
    boolean out = true;

    Connection connection = null;
    PreparedStatement stmt = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      String sql =
          "INSERT INTO service_instances  (INSTANCE_UUID, VIM_INSTANCE_UUID, VIM_INSTANCE_NAME,VIM_UUID) "
              + "VALUES (?, ?, ?, ?);";
      stmt = connection.prepareStatement(sql);
      stmt.setString(1, instanceUuid);
      stmt.setString(2, vimInstanceUuid);
      stmt.setString(3, vimInstanceName);
      stmt.setString(4, vimUuid);
      stmt.executeUpdate();
      connection.commit();
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        out = false;
      }
    }
    if (!out) {
      Logger.info("Service instance written successfully");
    }

    return out;
  }

  /**
   * Write the wrapper record into the repository with the specified UUID.
   * 
   * @param uuid the UUID of the wrapper to store
   * @param wrapper the WrapperRecord object with the information on the wrapper to store
   * 
   * @return true for process success
   */
  public boolean writeVimEntry(String uuid, Wrapper wrapper) {
    boolean out = true;

    Connection connection = null;
    PreparedStatement stmt = null;
    try {
      Class.forName("org.postgresql.Driver");
      connection =
          DriverManager.getConnection(
              "jdbc:postgresql://" + prop.getProperty("repo_host") + ":"
                  + prop.getProperty("repo_port") + "/" + "vimregistry",
              prop.getProperty("user"), prop.getProperty("pass"));
      connection.setAutoCommit(false);

      String sql = "INSERT INTO VIM "
          + "(UUID, NAME, TYPE, VENDOR, ENDPOINT, USERNAME, CONFIGURATION, CITY, COUNTRY, PASS, AUTHKEY, DOMAIN) "
          + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);";
      stmt = connection.prepareStatement(sql);
      stmt.setString(1, uuid);
      stmt.setString(2, wrapper.getConfig().getName());
      stmt.setString(3, wrapper.getConfig().getWrapperType().toString());
      stmt.setString(4, wrapper.getConfig().getVimVendor().toString());
      stmt.setString(5, wrapper.getConfig().getVimEndpoint().toString());
      stmt.setString(6, wrapper.getConfig().getAuthUserName());
      stmt.setString(7, wrapper.getConfig().getConfiguration());
      stmt.setString(8, wrapper.getConfig().getCity());
      stmt.setString(9, wrapper.getConfig().getCountry());
      stmt.setString(10, wrapper.getConfig().getAuthPass());
      stmt.setString(11, wrapper.getConfig().getAuthKey());
      stmt.setString(12, wrapper.getConfig().getDomain());

      stmt.executeUpdate();
      connection.commit();
    } catch (SQLException e) {
      Logger.error(e.getMessage());
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
        Logger.error(e.getMessage());
        out = false;
      }
    }
    Logger.info("VIM Wrapper written successfully");

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
      Logger.error("Unable to load Postregs Config file", e);
    }

    return prop;
  }

}
