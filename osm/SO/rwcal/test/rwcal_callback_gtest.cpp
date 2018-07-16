
/*
 * 
 *   Copyright 2016 RIFT.IO Inc
 *
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 */



#include <rwut.h>

#include "rwcal-api.h"

struct test_struct {
  int accessed;
};

struct test_struct g_test_struct;

class RWCalCallbackTest : public ::testing::Test {
  /*
   * This is a tough one to test as we're really relying on the
   * gobject introspection to do all the data marshalling for us
   * correctly.  At this point, all I can think of to do is to
   * just create a closure and then call it the same way it would
   * typically be called in C and make sure that everything
   * executed as expected.
   */
 protected:
  rwcal_module_ptr_t rwcal;

  virtual void SetUp() {
    rwcal = rwcal_module_alloc();
    ASSERT_TRUE(rwcal);

    g_test_struct.accessed = 0;
  }

  virtual void TearDown() {
    rwcal_module_free(&rwcal);
  }

  virtual void TestSuccess() {
    ASSERT_TRUE(rwcal);
#if 0
    rwcal_closure_ptr_t closure;

    closure = rwcal_closure_alloc(
        rwcal,
        &update_accessed,
        (void *)&g_test_struct);
    ASSERT_TRUE(closure);

    ASSERT_EQ(g_test_struct.accessed, 0);
    rw_cal_closure_callback(closure);
    ASSERT_EQ(g_test_struct.accessed, 1);

    rwcal_closure_free(&closure);
    ASSERT_FALSE(closure);
#endif
  }
};


TEST_F(RWCalCallbackTest, TestSuccess) {
  TestSuccess();
}
